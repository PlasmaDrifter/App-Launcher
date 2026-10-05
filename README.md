# AutoLaunch

AutoLaunch is a native PyQt6 desktop application designed to launch on boot or login, present a configurable checklist of applications with profiles and a countdown timer, launch the selected applications in decoupled background sessions, and cleanly terminate itself.

## Key Features

- **Desktop Boot Autostart**: Integrates with FreeDesktop autostart (`~/.config/autostart/autolaunch.desktop`) using dynamic environment paths (no hardcoded usernames).
- **FreeDesktop App Browser**: Scans installed desktop applications across user directories, system directories, and Flatpaks with live search filtering.
- **Application Icon Fidelity**: Utilizes `gtk-launch` and `gio launch` for desktop applications so that desktop environments (such as KDE Plasma on Wayland) properly link running windows to their `.desktop` specifications, preserving custom taskbar and titlebar icons (e.g., Zen Browser profiles, qBittorrent WebUI).
- **Profiles**: Support for multiple profiles (e.g. Default, Work, Gaming) with the ability to create, switch, rename, and delete profiles.
- **Countdown Timer**: Automatically launches enabled applications after a configurable countdown (default: 5 seconds) unless paused or cancelled.
- **Startup Delays**: Individual applications can have staggered launch delays (e.g. 5s delay) to avoid system boot congestion.
- **Clean Self-Termination**: Closes immediately after launching all selected applications in detached background sessions.

## Installation

Run the installation script:

```bash
cd ~/Source/AutoLaunch
./install.sh
```

This creates:
- `~/.local/bin/autolaunch` executable link
- `~/.local/share/applications/autolaunch.desktop` application menu entry
- `~/.config/autostart/autolaunch.desktop` desktop autostart entry

## Usage

### GUI Mode
```bash
python3 autolaunch.py
```

### Config Mode (Skip Countdown)
```bash
python3 autolaunch.py --config
```

### Headless Mode (Launch active profile immediately without GUI)
```bash
python3 autolaunch.py --headless
```

## Running Tests

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```
