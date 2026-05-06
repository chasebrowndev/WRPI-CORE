# wrathsberrypi

Modular USB dongle framework for the Raspberry Pi Zero 2W.

Plug into a machine → SSH in over USB-ethernet → fire-themed TUI launches → run your tools.

---

## Deploy

```bash
git clone https://github.com/chasebrowndev/wrathsberrypi
cd wrathsberrypi
sudo bash setup.sh
```

Then reboot. SSH in from the host machine:

```bash
ssh weaver@weaver.local
```

The TUI launches automatically.

---

## How it works

- `rpi-usb-gadget` handles all USB gadget setup (ECM for Linux, RNDIS for Windows, HID). We don't touch it.
- `setup.sh` installs Python/Textual, drops the TUI, and hooks it to SSH login.
- Tools live in `/opt/weaver/tools/<toolname>/`.

---

## Adding a tool

Drop a folder into `tools/` with these files:

```
tools/
  mytool/
    manifest.toml   # name, description, version
    install.sh      # runs once if config.toml is missing
    main.py         # entry point, runs every time after install
```

The TUI auto-discovers it on next launch (or press `r` to refresh).

If `config.toml` doesn't exist when you select the tool, `install.sh` runs first and should create it on success. After that, `main.py` runs directly.

See `tools/_example/` for a minimal working template.

---

## Included tools

| Tool | Description |
|------|-------------|
| `tailscale` | Join the Pi to your Tailnet for remote access from anywhere |

---

## TUI keybinds

| Key | Action |
|-----|--------|
| `↑ ↓` | Navigate |
| `Enter` | Launch selected tool |
| `r` | Refresh tool list |
| `b` | Drop to bash shell |
| `q` | Quit TUI |

---

## Tailscale (post-setup)

```bash
sudo tailscale up
```

Opens an auth URL — open it on any device logged into your Tailscale account. After that the Pi stays on your tailnet across reboots.

From school or anywhere:

```bash
ssh weaver@weaver.tail<xxxxx>.ts.net
```
