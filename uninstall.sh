#!/bin/bash
# uninstall.sh — completely remove wrathsberrypi
# Requires sudo. Removes all traces.

if [ "$EUID" -ne 0 ]; then
    echo "Run with sudo: sudo bash uninstall.sh"
    exit 1
fi

USER="${SUDO_USER:-weaver}"
HOME_DIR="/home/$USER"

# ── Confirmation ──────────────────────────────────────────────────────────────
echo ""
echo "  ◈ wrathsberrypi uninstaller"
echo ""
echo "  This will remove:"
echo "    $HOME_DIR/.wrath/ (TUI, venv, all tools)"
echo "    SSH login hook from $HOME_DIR/.bashrc"
echo "    Boot config changes (optional)"
echo ""
read -p "  Are you sure? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "  Aborted."
    exit 0
fi

# ── Boot config ───────────────────────────────────────────────────────────────
echo ""
read -p "  Remove boot config changes (dtoverlay=dwc2, modules-load=dwc2)? [y/N] " boot_confirm

CONFIG_TXT="/boot/firmware/config.txt"
CMDLINE_TXT="/boot/firmware/cmdline.txt"

if [[ "$boot_confirm" == "y" || "$boot_confirm" == "Y" ]]; then
    if grep -q "dtoverlay=dwc2" "$CONFIG_TXT" 2>/dev/null; then
        sed -i '/dtoverlay=dwc2/d' "$CONFIG_TXT"
        echo "  - Removed dtoverlay=dwc2 from config.txt"
    fi
    if grep -q "modules-load=dwc2" "$CMDLINE_TXT" 2>/dev/null; then
        sed -i 's/ modules-load=dwc2//' "$CMDLINE_TXT"
        echo "  - Removed modules-load=dwc2 from cmdline.txt"
    fi
else
    echo "  ~ Boot config left intact."
fi

# ── SSH login hook ────────────────────────────────────────────────────────────
BASHRC="$HOME_DIR/.bashrc"

if grep -q "wrathsberrypi" "$BASHRC" 2>/dev/null; then
    sed -i '/# wrathsberrypi/,/^fi$/d' "$BASHRC"
    echo "  - Removed SSH login hook from $BASHRC"
fi

# ── .wrath directory ──────────────────────────────────────────────────────────
if [ -d "$HOME_DIR/.wrath" ]; then
    rm -rf "$HOME_DIR/.wrath"
    echo "  - Removed $HOME_DIR/.wrath"
fi

echo ""
echo "  ◈ Done. Reboot if you removed boot config changes."
echo ""
