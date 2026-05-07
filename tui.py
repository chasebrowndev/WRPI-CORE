#!/usr/bin/env python3
"""
wrathsberrypi — tool launcher
"""

import sys
import subprocess
import os
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import box

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

TOOLS_DIR = Path.home() / ".wrath/tools"
console   = Console()

O  = "#ff6a00"   # orange
D  = "#7a2a00"   # dim
D2 = "#994400"   # dim2


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


def draw(tools: list[dict]) -> None:
    os.system("clear")
    console.print(f"\n  [bold {O}]◈  WRATHSBERRY PI[/bold {O}]\n", highlight=False)

    if not tools:
        console.print(f"  [{D}]No tools found in ~/.wrath/tools/[/{D}]\n")
        return

    table = Table(
        box=box.SIMPLE,
        show_header=False,
        padding=(0, 2),
        expand=False,
    )
    table.add_column(style=f"bold {D2}", width=4)   # index
    table.add_column(style=f"bold {O}",  width=22)  # name
    table.add_column(style=D2,           width=40)  # description
    table.add_column(style=D)                        # status

    for i, t in enumerate(tools, 1):
        m    = t["manifest"]
        name = m.get("name", t["path"].name)
        desc = m.get("description", "")

        if t["ready"]:
            badge = f"[{O}]● ready[/{O}]"
        elif t["has_installer"]:
            badge = f"[{D}]○ needs setup[/{D}]"
        else:
            badge = f"[{D}]○ no installer[/{D}]"

        table.add_row(str(i), name, desc, badge)

    console.print(table)
    console.print(
        f"  [{D}]enter number to launch  ·  s=shell  ·  r=refresh  ·  q=quit[/{D}]\n",
        highlight=False,
    )


def run_tool(tool: dict) -> None:
    path    = tool["path"]
    config  = path / "config.toml"
    install = path / "install.sh"
    main    = path / "main.py"
    name    = tool["manifest"].get("name", path.name)

    os.system("clear")

    # Install phase
    if not config.exists():
        if not install.exists():
            console.print(f"\n  [red]◈ {name}: no install.sh found.[/red]")
            input("\n  Press Enter to return...")
            return

        needs_root = tool["manifest"].get("requires_root", False)
        console.print(f"\n  [{O}]◈ Setting up {name}...[/{O}]\n", highlight=False)
        cmd    = ["sudo", "bash", str(install)] if needs_root else ["bash", str(install)]
        result = subprocess.run(cmd, cwd=str(path))

        if result.returncode != 0:
            console.print(f"\n  [red]◈ Setup failed (exit {result.returncode}).[/red]")
            input("\n  Press Enter to return...")
            return

        console.print(f"\n  [{O}]◈ Setup complete.[/{O}]\n", highlight=False)

    # Run phase
    if not main.exists():
        console.print(f"\n  [red]◈ {name}: no main.py found.[/red]")
        input("\n  Press Enter to return...")
        return

    venv_py = Path.home() / ".wrath/venv/bin/python3"
    python  = str(venv_py) if venv_py.exists() else sys.executable
    subprocess.run([python, str(main)], cwd=str(path))


def shell() -> None:
    os.system("clear")
    console.print(f"  [{O}]◈ Weaver shell — type 'exit' to return.[/{O}]\n", highlight=False)
    subprocess.run([os.environ.get("SHELL", "/bin/bash")])


def main() -> None:
    tools = discover_tools()

    while True:
        draw(tools)

        try:
            raw = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if raw == "q":
            break
        elif raw == "s":
            shell()
            tools = discover_tools()
        elif raw == "r":
            tools = discover_tools()
        elif raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(tools):
                run_tool(tools[idx])
                tools = discover_tools()
            else:
                console.print(f"  [red]No tool {raw}.[/red]")
                input("  Press Enter to continue...")
        elif raw:
            pass  # ignore unknown input, just redraw

    os.system("clear")


if __name__ == "__main__":
    main()
