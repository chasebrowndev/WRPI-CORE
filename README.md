# wrathsberrypi

Modular USB dongle framework for the Raspberry Pi 5.

Plug into a machine → SSH in over USB-ethernet → fire-themed TUI launches → run your tools.

---

## Deploy

```bash
git clone https://github.com/chasebrowndev/WRPI-CORE
cd WRPI-CORE
sudo bash setup.sh
```

Then reboot. SSH in from the host machine:

```bash
ssh <username>@<hostname>.local
```

The TUI launches automatically.

---

## How it works

- Downloaded tools are sorted into categories specified in their metadata.
- If no category is specified they are thrown in general.
- Tools live in `~/.wrath/tools/<toolname>/`.

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

## Basic tool suit

- Tailscale | for use with your tailnet.
- Tailnet Forwarding | Shares tailnet connection with host device.
- usb-gadget | Activates gadget mode, a dep for many other tools.

---

## TUI keybinds

- Arrow keys | Menu nav
- Enter | Interact
- r | refresh
- s | drop to shell
- b | back
- q | quit


---
