#!/usr/bin/env python3
"""
wrathsberrypi TUI — modular tool launcher.
↑↓ navigate · enter launch · b shell · r refresh · q quit
"""

import sys
import subprocess
import os
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import ListView, ListItem, Label, Static
from textual.containers import Horizontal, Vertical
from textual.binding import Binding
from textual.reactive import reactive

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

TOOLS_DIR = Path.home() / ".wrath/tools"

# ── Theme ──────────────────────────────────────────────────────────────────────
MAIN       = "#ff6a00"
ACCENT     = "#ff2200"
BG         = "#0d0000"
BG_RAISED  = "#1a0500"
BG_SELECT  = "#2d0800"
BORDER     = "#3d0a00"
BORDER_HL  = "#8b1a00"
DIM        = "#7a2a00"
DIM2       = "#994400"
# ──────────────────────────────────────────────────────────────────────────────

CSS = f"""
Screen {{
    background: {BG};
    layout: vertical;
}}

#header {{
    height: 3;
    background: {BG_RAISED};
    border-bottom: solid {BORDER_HL};
    color: {MAIN};
    text-style: bold;
    content-align: center middle;
}}

#body {{
    layout: horizontal;
    height: 1fr;
}}

#tool-list {{
    width: 40;
    background: {BG};
    border-right: solid {BORDER};
    padding: 0 0;
}}

ListView {{
    background: {BG};
}}

ListItem {{
    background: {BG};
    padding: 0 2;
    height: 3;
    border-bottom: solid {BG_RAISED};
}}

ListItem:hover {{
    background: {BG_RAISED};
}}

ListItem.--highlight {{
    background: {BG_SELECT};
    border-left: solid {MAIN};
}}

.item-name {{
    color: {MAIN};
    text-style: bold;
}}

.item-meta {{
    color: {DIM2};
}}

.item-badge-ready {{
    color: {MAIN};
}}

.item-badge-new {{
    color: {DIM};
}}

#detail-panel {{
    width: 1fr;
    background: {BG};
    padding: 2 3;
}}

#detail-name {{
    color: {MAIN};
    text-style: bold;
    height: 2;
}}

#detail-desc {{
    color: {DIM2};
    height: 2;
}}

#detail-meta {{
    color: {DIM};
    height: 1;
}}

#detail-status {{
    color: {MAIN};
    height: 2;
    margin-top: 1;
}}

#detail-hint {{
    color: {DIM};
    margin-top: 2;
    height: 3;
}}

#statusbar {{
    height: 1;
    background: {BG_RAISED};
    border-top: solid {BORDER_HL};
    color: {DIM2};
    content-align: left middle;
    padding: 0 2;
}}

Footer {{
    background: {BG_RAISED};
    color: {DIM};
}}

Footer > .footer--key {{
    background: {BORDER};
    color: {MAIN};
}}
"""


def load_manifest(tool_path: Path) -> dict:
    manifest = tool_path / "manifest.toml"
    if not manifest.exists():
        return {"name": tool_path.name, "description": "", "version": "?", "author": ""}
    if tomllib is None:
        data = {}
        for line in manifest.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                data[k.strip()] = v.strip().strip('"')
        return data
    with open(manifest, "rb") as f:
        return tomllib.load(f)


def discover_tools() -> list[dict]:
    if not TOOLS_DIR.exists():
        return []
    tools = []
    for entry in sorted(TOOLS_DIR.iterdir()):
        if entry.is_dir() and not entry.name.startswith("_"):
            manifest = load_manifest(entry)
            tools.append({
                "path": entry,
                "manifest": manifest,
                "ready": (entry / "config.toml").exists(),
                "has_installer": (entry / "install.sh").exists(),
                "has_main": (entry / "main.py").exists(),
            })
    return tools


class ToolItem(ListItem):
    def __init__(self, tool: dict):
        super().__init__()
        self.tool = tool

    def compose(self) -> ComposeResult:
        m = self.tool["manifest"]
        name = m.get("name", self.tool["path"].name)
        desc = m.get("description", "")
        short_desc = (desc[:28] + "…") if len(desc) > 30 else desc

        if self.tool["ready"]:
            badge, badge_cls = "● ready", "item-badge-ready"
        elif self.tool["has_installer"]:
            badge, badge_cls = "○ needs setup", "item-badge-new"
        else:
            badge, badge_cls = "○ no installer", "item-badge-new"

        yield Vertical(
            Label(f" {name}", classes="item-name"),
            Label(f" {short_desc}  [{badge}]", classes=f"item-meta {badge_cls}"),
        )


class WeaverApp(App):
    CSS = CSS
    TITLE = "WEAVER"
    BINDINGS = [
        Binding("enter", "launch", "Launch"),
        Binding("b", "shell", "Shell"),
        Binding("r", "refresh", "Refresh"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.tools: list[dict] = []

    def compose(self) -> ComposeResult:
        yield Static("  ◈  W R A T H S B E R R Y P I  ◈", id="header")
        with Horizontal(id="body"):
            with Vertical(id="tool-list"):
                yield ListView(id="lv")
            with Vertical(id="detail-panel"):
                yield Static("", id="detail-name")
                yield Static("", id="detail-desc")
                yield Static("", id="detail-meta")
                yield Static("", id="detail-status")
                yield Static("", id="detail-hint")
        yield Static("", id="statusbar")

    def on_mount(self) -> None:
        self._load_tools()

    def _load_tools(self) -> None:
        self.tools = discover_tools()
        lv = self.query_one("#lv", ListView)
        lv.clear()
        if not self.tools:
            lv.mount(Static("  No tools in ~/.wrath/tools/", classes="item-meta"))
            self._clear_detail()
        else:
            for tool in self.tools:
                lv.mount(ToolItem(tool))
        self._update_statusbar()

    def _update_statusbar(self, msg: str = "") -> None:
        bar = self.query_one("#statusbar", Static)
        if msg:
            bar.update(f"  {msg}")
        else:
            total = len(self.tools)
            ready = sum(1 for t in self.tools if t["ready"])
            bar.update(f"  {total} tool{'s' if total != 1 else ''}  ·  {ready} ready")

    def _clear_detail(self) -> None:
        self.query_one("#detail-name",   Static).update("")
        self.query_one("#detail-desc",   Static).update("")
        self.query_one("#detail-meta",   Static).update("")
        self.query_one("#detail-status", Static).update("")
        self.query_one("#detail-hint",   Static).update("")

    def _show_detail(self, tool: dict) -> None:
        m = tool["manifest"]
        name    = m.get("name", tool["path"].name)
        desc    = m.get("description", "no description")
        version = m.get("version", "?")
        author  = m.get("author", "")
        meta    = f"v{version}"
        if author:
            meta += f"  ·  {author}"

        if tool["ready"]:
            status = "● Ready to launch"
            hint   = "Press [enter] to run."
        elif tool["has_installer"]:
            status = "○ Not set up yet"
            hint   = "Press [enter] to run the installer, then launch."
        else:
            status = "○ No installer found"
            hint   = "Drop an install.sh into this tool's folder to enable setup."

        if not tool["has_main"]:
            hint += "\n  ⚠ No main.py — tool will not run."

        self.query_one("#detail-name",   Static).update(f"  {name}")
        self.query_one("#detail-desc",   Static).update(f"  {desc}")
        self.query_one("#detail-meta",   Static).update(f"  {meta}")
        self.query_one("#detail-status", Static).update(f"\n  {status}")
        self.query_one("#detail-hint",   Static).update(f"\n  {hint}")

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item and isinstance(event.item, ToolItem):
            self._show_detail(event.item.tool)
            self._update_statusbar(event.item.tool["manifest"].get("name", ""))
        else:
            self._clear_detail()

    def action_launch(self) -> None:
        lv = self.query_one("#lv", ListView)
        item = lv.highlighted_child
        if item and isinstance(item, ToolItem):
            self._run_tool(item.tool)

    def _run_tool(self, tool: dict) -> None:
        path    = tool["path"]
        config  = path / "config.toml"
        install = path / "install.sh"
        main    = path / "main.py"
        name    = tool["manifest"].get("name", path.name)

        self.suspend()
        try:
            os.system("clear")

            # ── Install phase ──────────────────────────────────────────────
            if not config.exists() and install.exists():
                print(f"\n\033[38;5;208m◈ Setting up {name}...\033[0m\n")
                result = subprocess.run(["bash", str(install)], cwd=str(path))
                if result.returncode != 0:
                    print(f"\n\033[38;5;196m◈ Setup failed (exit {result.returncode}).\033[0m")
                    input("\n  Press Enter to return to Weaver...")
                    return
                print(f"\n\033[38;5;208m◈ Setup complete. Launching {name}...\033[0m\n")

            # ── Run phase ──────────────────────────────────────────────────
            if not main.exists():
                print(f"\n\033[38;5;196m◈ {name} has no main.py.\033[0m")
                print(f"  Add a main.py to {path} to make this tool runnable.")
                input("\n  Press Enter to return to Weaver...")
                return

            venv_python = Path.home() / ".wrath/venv/bin/python3"
            python = str(venv_python) if venv_python.exists() else sys.executable
            subprocess.run([python, str(main)], cwd=str(path))

        finally:
            self.resume()
            self._load_tools()
            lv = self.query_one("#lv", ListView)
            for i, t in enumerate(self.tools):
                if t["path"] == tool["path"]:
                    lv.index = i
                    self._show_detail(t)
                    break

    def action_shell(self) -> None:
        self.suspend()
        os.system("clear")
        print("\033[38;5;208m◈ Weaver shell. Type 'exit' to return.\033[0m\n")
        subprocess.run([os.environ.get("SHELL", "/bin/bash")])
        self.resume()

    def action_refresh(self) -> None:
        self._load_tools()
        self._update_statusbar("refreshed.")

    def action_quit(self) -> None:
        self.exit()


if __name__ == "__main__":
    WeaverApp().run()
