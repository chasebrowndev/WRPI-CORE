#!/bin/bash
# setup.sh — wrathsberrypi base install
# Run once on a fresh Pi image: sudo bash setup.sh

set -e

WEAVER_DIR="$HOME/.wrath"
TOOLS_DIR="$WEAVER_DIR/tools"
TUI_SCRIPT="$WEAVER_DIR/tui.py"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
USER="${SUDO_USER:-weaver}"
HOME_DIR="/home/$USER"

echo "=== wrathsberrypi setup ==="

# ── USB Gadget boot config ─────────────────────────────────────────────────────
echo "[0/5] Configuring USB gadget boot params..."

CONFIG_TXT="/boot/firmware/config.txt"
CMDLINE_TXT="/boot/firmware/cmdline.txt"

if ! grep -q "dtoverlay=dwc2" "$CONFIG_TXT" 2>/dev/null; then
    echo "" >> "$CONFIG_TXT"
    echo "dtoverlay=dwc2" >> "$CONFIG_TXT"
    echo "  + dtoverlay=dwc2 added to config.txt"
else
    echo "  ~ dtoverlay=dwc2 already present"
fi

if ! grep -q "modules-load=dwc2" "$CMDLINE_TXT" 2>/dev/null; then
    sed -i 's/rootwait/rootwait modules-load=dwc2/' "$CMDLINE_TXT"
    echo "  + modules-load=dwc2 added to cmdline.txt"
else
    echo "  ~ modules-load=dwc2 already present"
fi

# ── Dependencies ──────────────────────────────────────────────────────────────
echo "[1/5] Installing dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv openssh-server git curl

# ── Python venv ───────────────────────────────────────────────────────────────
echo "[2/5] Setting up Python environment..."
mkdir -p "$WEAVER_DIR"
python3 -m venv "$WEAVER_DIR/venv"
"$WEAVER_DIR/venv/bin/pip" install --quiet textual tomli

# ── Tools directory ───────────────────────────────────────────────────────────
echo "[3/5] Installing tools..."
mkdir -p "$TOOLS_DIR"

# Copy tools from repo into place (skip if already there)
for tool_src in "$REPO_DIR/tools"/*/; do
    tool_name="$(basename "$tool_src")"
    tool_dst="$TOOLS_DIR/$tool_name"
    if [ ! -d "$tool_dst" ]; then
        cp -r "$tool_src" "$tool_dst"
        echo "  + $tool_name"
    else
        echo "  ~ $tool_name (already exists, skipping)"
    fi
done

chown -R "$USER:$USER" "$WEAVER_DIR"

# ── TUI ───────────────────────────────────────────────────────────────────────
echo "[4/5] Installing TUI..."
cp "$REPO_DIR/tui.py" "$TUI_SCRIPT"
cp "$REPO_DIR/uninstall.sh" "$WEAVER_DIR/uninstall.sh"
chmod +x "$TUI_SCRIPT" "$WEAVER_DIR/uninstall.sh"
chown "$USER:$USER" "$TUI_SCRIPT" "$WEAVER_DIR/uninstall.sh"

# ── SSH login hook ────────────────────────────────────────────────────────────
echo "[5/5] Wiring TUI to SSH login..."

BASHRC="$HOME_DIR/.bashrc"
BLOCK='
# wrathsberrypi — launch TUI on interactive SSH login
if [[ -n "$SSH_CONNECTION" ]] && [[ $- == *i* ]] && [[ -z "$WEAVER_SHELL" ]]; then
    export WEAVER_SHELL=1
    $HOME/.wrath/venv/bin/python3 $HOME/.wrath/tui.py
fi
'

if ! grep -q "wrathsberrypi" "$BASHRC" 2>/dev/null; then
    echo "$BLOCK" >> "$BASHRC"
fi
chown "$USER:$USER" "$BASHRC"

# ── Hostname ──────────────────────────────────────────────────────────────────
hostnamectl set-hostname weaver 2>/dev/null || true

echo ""
echo "=== Done ==="
echo ""
echo "  SSH:    ssh weaver@weaver.local"
echo "  Tools:  $HOME/.wrath/tools/"
echo "  TUI:    auto-launches on SSH login"
echo ""
echo "  To add a tool later:"
echo "    cp -r tools/mytool $HOME/.wrath/tools/"
echo ""
echo "  Reboot to apply."
echo ""
