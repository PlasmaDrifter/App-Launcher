#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
APP_DIR="${HOME}/.local/share/applications"
AUTOSTART_DIR="${HOME}/.config/autostart"

mkdir -p "${BIN_DIR}" "${APP_DIR}" "${AUTOSTART_DIR}"

# 1. Install CLI wrapper / symlink in ~/.local/bin
cat <<'EOF' > "${BIN_DIR}/autolaunch"
#!/bin/bash
exec python3 "${HOME}/Source/AutoLaunch/autolaunch.py" "$@"
EOF
chmod +x "${BIN_DIR}/autolaunch"
chmod +x "${SCRIPT_DIR}/autolaunch.py"

# 2. Install application menu desktop file
cat <<EOF > "${APP_DIR}/autolaunch.desktop"
[Desktop Entry]
Type=Application
Version=1.0
Name=AutoLaunch
GenericName=Startup Application Launcher
Comment=Configure and launch startup applications on desktop boot
Exec=sh -c 'python3 "\$HOME/Source/AutoLaunch/autolaunch.py"'
Icon=system-run
Terminal=false
StartupNotify=true
Categories=Utility;System;
StartupWMClass=autolaunch
X-KDE-Wayland-AppId=autolaunch
EOF
chmod 644 "${APP_DIR}/autolaunch.desktop"

# 3. Install desktop autostart entry
cat <<EOF > "${AUTOSTART_DIR}/autolaunch.desktop"
[Desktop Entry]
Type=Application
Version=1.0
Name=AutoLaunch
GenericName=Startup Application Launcher
Comment=Configure and launch startup applications on desktop boot
Exec=sh -c 'python3 "\$HOME/Source/AutoLaunch/autolaunch.py" --autostart'
Icon=system-run
Terminal=false
StartupNotify=true
Categories=Utility;System;
X-GNOME-Autostart-enabled=true
StartupWMClass=autolaunch
X-KDE-Wayland-AppId=autolaunch
EOF
chmod 644 "${AUTOSTART_DIR}/autolaunch.desktop"

echo "AutoLaunch installed successfully."
echo "Binary link: ${BIN_DIR}/autolaunch"
echo "Menu entry: ${APP_DIR}/autolaunch.desktop"
echo "Autostart:  ${AUTOSTART_DIR}/autolaunch.desktop"
