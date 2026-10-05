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
Exec=autolaunch
Icon=autolaunch
Terminal=false
StartupNotify=true
Categories=LocalTools;
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
Exec=autolaunch --autostart
Icon=autolaunch
Terminal=false
StartupNotify=true
Categories=LocalTools;
X-GNOME-Autostart-enabled=true
StartupWMClass=autolaunch
X-KDE-Wayland-AppId=autolaunch
EOF
chmod 644 "${AUTOSTART_DIR}/autolaunch.desktop"

# 4. Install icons into user icon theme
ICON_SCALABLE_DIR="${HOME}/.local/share/icons/hicolor/scalable/apps"
mkdir -p "${ICON_SCALABLE_DIR}"
if [ -f "${SCRIPT_DIR}/assets/autolaunch.svg" ]; then
    cp "${SCRIPT_DIR}/assets/autolaunch.svg" "${ICON_SCALABLE_DIR}/autolaunch.svg"
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "${HOME}/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "AutoLaunch installed successfully."
echo "Binary link: ${BIN_DIR}/autolaunch"
echo "Menu entry: ${APP_DIR}/autolaunch.desktop"
echo "Autostart:  ${AUTOSTART_DIR}/autolaunch.desktop"
echo "Icon:       ${ICON_SCALABLE_DIR}/autolaunch.svg"
