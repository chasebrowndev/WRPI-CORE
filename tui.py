#!/usr/bin/env python3
"""
wrathsberrypi TUI — modular tool launcher.
Arrow keys + enter to navigate. b=shell, r=refresh, q=quit.

Theme: edit MAIN and ACCENT below to reskin.
"""

import sys
import subprocess
import os
from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import ListView, ListItem, Label, Static
from textual.containers import Vertical
from textual.binding import Binding

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

TOOLS_DIR = Path.home() / ".wrath/tools"

# ── Theme ─────────────────────────────────────────────────────────────────────
# Edit these two to reskin the entire TUI.
MAIN   = "#ff6a00"   # primary text, highlights, selected border
ACCENT = "#ff2200"   # status indicators, key hints, dim elements

# Derived shades — adjust if needed
BG         = "#0d0000"
BG_RAISED  = "#1a0500"
BG_SELECT  = "#2d0800"
BORDER     = "#3d0a00"
BORDER_HL  = "#8b1a00"
DIM        = "#7a2a00"
DIM2       = "#994400"
# ─────────────────────────────────────────────────────────────────────────────

CSS = f"""
Screen {{
    background: {BG};
}}

#title {{
    height: 3;
    background: {BG_RAISED};
    border-bottom: solid {BORDER_HL};
    color: {MAIN};
    text-style: bold;
    content-align: center middle;
    padding: 0 2;
}}

#subtitle {{
    color: {DIM};
    content-align: center middle;
    padding-bottom: 1;
    height: 2;
}}

#tool-list {{
    background: {BG};
    border: solid {BORDER};
    margin: 0 4 1 4;
    padding: 1 2;
}}

ListItem {{
    background: {BG};
    padding: 1 2;
    border-bottom: solid {BG_RAISED};
}}

ListItem:hover {{
    background: {BG_RAISED};
}}

ListItem.--highlight {{
    background: {BG_SELECT};
    border-left: solid {MAIN};
}}

.tool-name {{
    color: {MAIN};
    text-style: bold;
}}

.tool-desc {{
    color: {DIM2};
    text-style: italic;
}}

.tool-status-installed {{
    color: {ACCENT};
}}

.tool-status-new {{
    color: {DIM};
}}

#status {{
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
        return {"name": tool_path.name, "description": "no manifest", "version": "?"}
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
                "path": entry,
                "manifest": load_manifest(entry),
                "installed": (entry / "config.toml").exists(),
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
        if self.tool["installed"]:
            status, cls = "● configured", "tool-status-installed"
        else:
            status, cls = "○ not configured", "tool-status-new"
        yield Vertical(
            Label(f"  {name}", classes="tool-name"),
            Label(f"  {desc}", classes="tool-desc"),
            Label(f"  {status}", classes=cls),
        )


class WeaverApp(App):
    CSS = CSS
    TITLE = "WEAVER"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("b", "shell", "Shell"),
        Binding("enter", "launch", "Launch"),
        Binding("r", "refresh", "Refresh"),
        Binding("ctrl+x", "uninstall", "Uninstall"),
    ]

    def __init__(self):
        super().__init__()
        self.tools: list[dict] = []

    def compose(self) -> ComposeResult:
        yield Static("  ◈ WRATHSBERRY PI  //  TOOL CONTROL  ◈", id="title")
        yield Static(
            "  ↑↓ navigate  ·  enter launch  ·  b shell  ·  r refresh  ·  q quit",
            id="subtitle",
        )
        yield ListView(id="tool-list")
        yield Static("", id="status")

    def on_mount(self) -> None:
        self._load_tools()

    def _load_tools(self) -> None:
        self.tools = discover_tools()
        lv = self.query_one("#tool-list", ListView)
        lv.clear()
        if not self.tools:
            lv.mount(Static("  No tools found in ~/.wrath/tools/"))
        else:
            for tool in self.tools:
                lv.mount(ToolItem(tool))
        self._set_status()

    def _set_status(self, msg: str = "") -> None:
        bar = self.query_one("#status", Static)
        if msg:
            bar.update(f"  {msg}")
        else:
            total = len(self.tools)
            configured = sum(1 for t in self.tools if t["installed"])
            bar.update(f"  {total} tools  ·  {configured} configured")

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item and isinstance(event.item, ToolItem):
            name = event.item.tool["manifest"].get("name", "")
            self._set_status(f"selected: {name}")

    def action_launch(self) -> None:
        lv = self.query_one("#tool-list", ListView)
        item = lv.highlighted_child
        if item and isinstance(item, ToolItem):
            self._run_tool(item.tool)

    def _run_tool(self, tool: dict) -> None:
        path = tool["path"]
        config  = path / "config.toml"
        install = path / "install.sh"
        main    = path / "main.py"

        self.suspend()
        try:
            if not config.exists() and install.exists():
                print(f"\n\033[38;5;208m◈ Installing {tool['manifest'].get('name', path.name)}...\033[0m\n")
                r = subprocess.run(["bash", str(install)], cwd=str(path))
                if r.returncode != 0:
                    print(f"\n\033[38;5;196m◈ Installer failed (exit {r.returncode})\033[0m")
                    input("\nPress Enter to return...")
                    return
                print(f"\n\033[38;5;208m◈ Done. Launching...\033[0m\n")

            if main.exists():
                subprocess.run([sys.executable, str(main)], cwd=str(path))
            else:
                print(f"\n\033[38;5;196m◈ No main.py in {path}\033[0m")
                input("\nPress Enter to return...")
        finally:
            self.resume()
            self._load_tools()

    def action_shell(self) -> None:
        self.suspend()
        print("\n\033[38;5;208m◈ Shell. Type 'exit' to return to Weaver.\033[0m\n")
        subprocess.run([os.environ.get("SHELL", "/bin/bash")])
        self.resume()

    def action_refresh(self) -> None:
        self._load_tools()
        self._set_status("refreshed.")

    def action_uninstall(self) -> None:
        self.suspend()
        print("\n\033[38;5;196m◈ Uninstall wrathsberrypi\033[0m\n")
        confirm = input("  This will remove all of wrathsberrypi. Are you sure? [y/N] ").strip().lower()
        if confirm == "y":
            import shutil
            uninstall = Path.home() / ".wrath/uninstall.sh"
            # Try repo path first, fall back to bundled copy
            candidates = [
                Path.home() / "wrathsberrypi/uninstall.sh",
                Path.home() / ".wrath/uninstall.sh",
            ]
            script = next((p for p in candidates if p.exists()), None)
            if script:
                subprocess.run(["sudo", "bash", str(script)])
            else:
                print("\n  \033[38;5;196mCould not find uninstall.sh.\033[0m")
                print("  Run manually: sudo bash ~/wrathsberrypi/uninstall.sh")
                input("\n  Press Enter to return...")
                self.resume()
                return
        else:
            print("  Aborted.")
            input("\n  Press Enter to return...")
        self.resume()

    def action_quit(self) -> None:
        self.exit()


if __name__ == "__main__":
    WeaverApp().run()
