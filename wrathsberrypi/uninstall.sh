#!/bin/bash
# uninstall.sh — completely remove wrathsberrypi
# Requires sudo. Removes all traces.

if [ "$EUID" -ne 0 ]; then
    echo "Run with sudo: sudo bash uninstall.sh"
    exit 1
fi

# ── Sudo auth confirmation ─────────────────────────────────────────────────────
echo ""
echo "  ◈ wrathsberrypi uninstaller"
echo ""
echo "  This will remove:"
echo "    /opt/weaver/ (TUI, venv, all tools)"
echo "    SSH login hook from ~/.bashrc"
echo "    Boot config changes (optional)"
echo ""
read -p "  Authenticate to continue. Are you sure? [y/N] " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "  Aborted."
    exit 0
fi

# ── Boot config ────────────────────────────────────────────────────────────────
echo ""
read -p "  Remove boot config changes (dtoverlay=dwc2, modules-load=dwc2)? [y/N] " boot_confirm

CONFIG_TXT="/boot/firmware/config.txt"
CMDLINE_TXT="/boot/firmware/cmdline.txt"

if [[ "$boot_confirm" == "y" || "$boot_confirm" == "Y" ]]; then
    # Remove dtoverlay=dwc2 line from config.txt
    if grep -q "dtoverlay=dwc2" "$CONFIG_TXT" 2>/dev/null; then
        sed -i '/dtoverlay=dwc2/d' "$CONFIG_TXT"
        echo "  - Removed dtoverlay=dwc2 from config.txt"
    fi
    # Remove modules-load=dwc2 from cmdline.txt
    if grep -q "modules-load=dwc2" "$CMDLINE_TXT" 2>/dev/null; then
        sed -i 's/ modules-load=dwc2//' "$CMDLINE_TXT"
        echo "  - Removed modules-load=dwc2 from cmdline.txt"
    fi
else
    echo "  ~ Boot config left intact."
fi

# ── SSH login hook ─────────────────────────────────────────────────────────────
USER="${SUDO_USER:-weaver}"
BASHRC="/home/$USER/.bashrc"

if grep -q "wrathsberrypi" "$BASHRC" 2>/dev/null; then
    # Remove the block between the wrathsberrypi comment and the closing fi
    sed -i '/# wrathsberrypi/,/^fi$/d' "$BASHRC"
    echo "  - Removed SSH login hook from $BASHRC"
fi

# ── Weaver directory ───────────────────────────────────────────────────────────
if [ -d "/opt/weaver" ]; then
    rm -rf /opt/weaver
    echo "  - Removed /opt/weaver"
fi

# ── Done ───────────────────────────────────────────────────────────────────────
echo ""
echo "  ◈ wrathsberrypi removed."
echo ""
echo "  Reboot to apply boot config changes if selected."
echo ""
