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
from textual.widgets import ListView, ListItem, Label, Static, Footer
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

TOOLS_DIR = Path.home() / ".wrath/tools"

MAIN      = "#ff6a00"
BG        = "#0d0000"
BG_RAISED = "#1a0500"
BG_SEL    = "#2d0800"
BORDER    = "#3d0a00"
BORDER_HL = "#8b1a00"
DIM       = "#7a2a00"
DIM2      = "#994400"

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

#list-panel {{
    width: 36;
    border-right: solid {BORDER};
}}

ListView {{
    background: {BG};
    height: 1fr;
}}

ListItem {{
    background: {BG};
    padding: 0 1;
    height: 4;
    border-bottom: solid {BG_RAISED};
}}

ListItem:hover {{
    background: {BG_RAISED};
}}

ListItem.--highlight {{
    background: {BG_SEL};
    border-left: solid {MAIN};
}}

.item-name {{
    color: {MAIN};
    text-style: bold;
    padding: 1 1 0 1;
}}

.item-desc {{
    color: {DIM2};
    padding: 0 1;
}}

.item-badge {{
    color: {DIM};
    padding: 0 1;
}}

.item-badge-ready {{
    color: {MAIN};
    padding: 0 1;
}}

#detail-panel {{
    width: 1fr;
    padding: 2 3;
    background: {BG};
}}

#detail-name {{
    color: {MAIN};
    text-style: bold;
}}

#detail-version {{
    color: {DIM};
    margin-bottom: 1;
}}

#detail-desc {{
    color: {DIM2};
    margin-bottom: 1;
}}

#detail-status {{
    color: {MAIN};
    margin-bottom: 1;
}}

#detail-action {{
    color: {DIM};
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
            tools.append({
                "path":          entry,
                "manifest":      load_manifest(entry),
                "ready":         (entry / "config.toml").exists(),
                "has_installer": (entry / "install.sh").exists(),
                "has_main":      (entry / "main.py").exists(),
            })
    return tools


class ToolItem(ListItem):
    def __init__(self, tool: dict):
        super().__init__()
        self.tool = tool

    def compose(self) -> ComposeResult:
        m    = self.tool["manifest"]
        name = m.get("name", self.tool["path"].name)
        desc = m.get("description", "")
        desc = (desc[:28] + "…") if len(desc) > 30 else desc

        if self.tool["ready"]:
            badge     = "● ready"
            badge_cls = "item-badge-ready"
        elif self.tool["has_installer"]:
            badge     = "○ needs setup"
            badge_cls = "item-badge"
        else:
            badge     = "○ no installer"
            badge_cls = "item-badge"

        yield Label(name,  classes="item-name")
        yield Label(desc,  classes="item-desc")
        yield Label(badge, classes=badge_cls)


class WeaverApp(App):
    CSS = CSS
    BINDINGS = [
        Binding("enter",  "launch",  "Launch"),
        Binding("b",      "shell",   "Shell"),
        Binding("r",      "refresh", "Refresh"),
        Binding("q",      "quit",    "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.tools: list[dict] = []
        self._selected: int = 0   # track index ourselves

    def compose(self) -> ComposeResult:
        yield Static("  ◈  WRATHSBERRY PI  ◈", id="header")
        with Horizontal(id="body"):
            with Vertical(id="list-panel"):
                yield ListView(id="lv")
            with Vertical(id="detail-panel"):
                yield Static("", id="detail-name")
                yield Static("", id="detail-version")
                yield Static("", id="detail-desc")
                yield Static("", id="detail-status")
                yield Static("", id="detail-action")
        yield Static("", id="statusbar")
        yield Footer()

    def on_mount(self) -> None:
        self._load_tools()

    # ── Tool loading ───────────────────────────────────────────────────────────

    def _load_tools(self) -> None:
        self.tools = discover_tools()
        lv = self.query_one("#lv", ListView)
        lv.clear()
        if self.tools:
            for tool in self.tools:
                lv.mount(ToolItem(tool))
            # restore or clamp selection
            self._selected = min(self._selected, len(self.tools) - 1)
            lv.index = self._selected
            self._show_detail(self.tools[self._selected])
        else:
            self._clear_detail()
        self._update_bar()

    # ── Detail panel ──────────────────────────────────────────────────────────

    def _clear_detail(self) -> None:
        for wid in ("detail-name", "detail-version", "detail-desc",
                    "detail-status", "detail-action"):
            self.query_one(f"#{wid}", Static).update("")
        self.query_one("#detail-name", Static).update(
            "No tools found.\n\nDrop tool folders into ~/.wrath/tools/ and press [r]."
        )

    def _show_detail(self, tool: dict) -> None:
        m       = tool["manifest"]
        name    = m.get("name",        tool["path"].name)
        desc    = m.get("description", "No description.")
        version = m.get("version",     "?")
        author  = m.get("author",      "")

        ver_line = f"v{version}"
        if author:
            ver_line += f"  ·  {author}"
        if m.get("requires_root"):
            ver_line += "  ·  requires sudo"

        if tool["ready"]:
            status = "● Ready"
            action = "Press Enter to launch."
        elif tool["has_installer"]:
            status = "○ Not installed"
            action = "Press Enter to install, then launch."
        else:
            status = "○ No installer"
            action = "Add an install.sh to set this tool up."

        if not tool["has_main"]:
            action = "⚠  No main.py — cannot run."

        self.query_one("#detail-name",    Static).update(name)
        self.query_one("#detail-version", Static).update(ver_line)
        self.query_one("#detail-desc",    Static).update(desc)
        self.query_one("#detail-status",  Static).update(status)
        self.query_one("#detail-action",  Static).update(action)

    # ── Status bar ────────────────────────────────────────────────────────────

    def _update_bar(self, msg: str = "") -> None:
        bar = self.query_one("#statusbar", Static)
        if msg:
            bar.update(f"  {msg}")
        else:
            total = len(self.tools)
            ready = sum(1 for t in self.tools if t["ready"])
            bar.update(f"  {total} tool{'s' if total != 1 else ''}  ·  {ready} ready")

    # ── Events ────────────────────────────────────────────────────────────────

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item and isinstance(event.item, ToolItem):
            self._selected = self.tools.index(event.item.tool)
            self._show_detail(event.item.tool)

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_launch(self) -> None:
        if not self.tools:
            return
        self._run_tool(self.tools[self._selected])

    def _run_tool(self, tool: dict) -> None:
        path    = tool["path"]
        config  = path / "config.toml"
        install = path / "install.sh"
        main    = path / "main.py"
        name    = tool["manifest"].get("name", path.name)

        self.suspend()
        try:
            os.system("clear")

            # Install
            if not config.exists():
                if not install.exists():
                    print(f"\n\033[38;5;196m◈ {name}: no install.sh found.\033[0m")
                    input("\n  Press Enter to return...")
                    return
                needs_root = tool["manifest"].get("requires_root", False)
                print(f"\n\033[38;5;208m◈ Setting up {name}...\033[0m\n")
                cmd = ["sudo", "bash", str(install)] if needs_root else ["bash", str(install)]
                result = subprocess.run(cmd, cwd=str(path))
                if result.returncode != 0:
                    print(f"\n\033[38;5;196m◈ Setup failed (exit {result.returncode}).\033[0m")
                    input("\n  Press Enter to return...")
                    return
                print(f"\n\033[38;5;208m◈ Setup complete.\033[0m\n")
                if not main.exists():
                    input("\n  Press Enter to return...")
                    return

            # Run
            if not main.exists():
                print(f"\n\033[38;5;196m◈ {name}: no main.py found.\033[0m")
                input("\n  Press Enter to return...")
                return

            venv_py = Path.home() / ".wrath/venv/bin/python3"
            python  = str(venv_py) if venv_py.exists() else sys.executable
            subprocess.run([python, str(main)], cwd=str(path))

        finally:
            self.resume()
            self._load_tools()

    def action_shell(self) -> None:
        self.suspend()
        os.system("clear")
        print("\033[38;5;208m◈ Weaver shell — type 'exit' to return.\033[0m\n")
        subprocess.run([os.environ.get("SHELL", "/bin/bash")])
        self.resume()

    def action_refresh(self) -> None:
        self._load_tools()
        self._update_bar("Refreshed.")

    def action_quit(self) -> None:
        self.exit()


if __name__ == "__main__":
    WeaverApp().run()
