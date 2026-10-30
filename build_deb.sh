#!/usr/bin/env bash
# Baut ein komplettes Debian/Ubuntu Installationspaket (dist/localdarts_1.0.0_amd64.deb)
# inklusive aller vorinstallierten Python-Abhängigkeiten, Desktop-Icon und /usr/bin/localdarts Starter.
set -e
cd "$(dirname "$0")"

PKG_NAME="localdarts"
PKG_VER="1.0.0"
ARCH="amd64"
DEB_NAME="${PKG_NAME}_${PKG_VER}_${ARCH}"
STAGE_DIR="dist/deb_build/${DEB_NAME}"
OUT_DEB="dist/${DEB_NAME}.deb"

echo "=================================================================="
echo "📦 Baue Debian/Ubuntu Paket: ${OUT_DEB}"
echo "=================================================================="

rm -rf "dist/deb_build" "${OUT_DEB}"
mkdir -p "${STAGE_DIR}/DEBIAN"
mkdir -p "${STAGE_DIR}/opt/localdarts/site-packages"
mkdir -p "${STAGE_DIR}/usr/bin"
mkdir -p "${STAGE_DIR}/usr/share/applications"
mkdir -p "${STAGE_DIR}/usr/share/icons/hicolor/scalable/apps"

echo "[1/5] Kopiere Anwendungsdateien nach /opt/localdarts..."
cp -r backend frontend run_app.py requirements.txt README.md HILFE_ANLEITUNG.md "${STAGE_DIR}/opt/localdarts/"
find "${STAGE_DIR}/opt/localdarts" -name "__pycache__" -type d -exec rm -rf {} +

echo "[2/5] Kopiere vorinstallierte Python-Bibliotheken (OpenCV, FastAPI, NumPy, Uvicorn)..."
SITE_PKGS=$(find .venv/lib -name "site-packages" -type d | head -n 1)
cp -r "${SITE_PKGS}/"* "${STAGE_DIR}/opt/localdarts/site-packages/"
find "${STAGE_DIR}/opt/localdarts/site-packages" -name "__pycache__" -type d -exec rm -rf {} +

echo "[3/5] Erstelle /usr/bin/localdarts Starter & Desktop-Icon..."
cat > "${STAGE_DIR}/usr/bin/localdarts" << 'EOF'
#!/usr/bin/env bash
export LOCALDARTS_CONFIG_DIR="${HOME}/.config/localdarts"
mkdir -p "${LOCALDARTS_CONFIG_DIR}"

# Wenn LocalDarts bereits auf Port 8000 läuft, einfach Browser öffnen:
if curl -s http://localhost:8000/api/status >/dev/null 2>&1; then
  xdg-open "http://localhost:8000" >/dev/null 2>&1 &
  exit 0
fi

cd /opt/localdarts
export PYTHONPATH="/opt/localdarts:/opt/localdarts/site-packages:${PYTHONPATH}"
exec /usr/bin/python3 /opt/localdarts/run_app.py "$@"
EOF
chmod 0755 "${STAGE_DIR}/usr/bin/localdarts"

# SVG App-Icon erstellen
cat > "${STAGE_DIR}/usr/share/icons/hicolor/scalable/apps/localdarts.svg" << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <circle cx="64" cy="64" r="60" fill="#101622" stroke="#00d48a" stroke-width="5"/>
  <circle cx="64" cy="64" r="44" fill="#d92b2b" stroke="#e2e8f0" stroke-width="2"/>
  <circle cx="64" cy="64" r="30" fill="#e5dec9" stroke="#e2e8f0" stroke-width="2"/>
  <circle cx="64" cy="64" r="17" fill="#169c46" stroke="#e2e8f0" stroke-width="2"/>
  <circle cx="64" cy="64" r="7" fill="#d92b2b" stroke="#ffffff" stroke-width="1.5"/>
</svg>
EOF

# Desktop-Eintrag erstellen
cat > "${STAGE_DIR}/usr/share/applications/localdarts.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=LocalDarts
GenericName=Lokales Autodarts System
Comment=Lokales 3-Kamera Dart-Erkennungssystem mit 16 Spielen (1-6 Spieler)
Exec=/usr/bin/localdarts
Icon=localdarts
Terminal=true
Categories=Game;SportsGame;
Keywords=darts;autodarts;scoreboard;opencv;
EOF

echo "[4/5] Erstelle DEBIAN/control und Paket-Metadaten..."
INSTALLED_SIZE=$(du -sk "${STAGE_DIR}/opt" "${STAGE_DIR}/usr" | awk '{s+=$1} END {print s}')

cat > "${STAGE_DIR}/DEBIAN/control" << EOF
Package: ${PKG_NAME}
Version: ${PKG_VER}
Section: games
Priority: optional
Architecture: ${ARCH}
Installed-Size: ${INSTALLED_SIZE}
Depends: python3 (>= 3.10)
Maintainer: Uwe Benzelrath <16435589+uwebenzelrath@users.noreply.github.com>
Homepage: https://github.com/uWiiiDev/LocalDarts
Description: LocalDarts - Lokales 3-Kamera Autodarts System
 Komplett lokales Steeldart-Erkennungssystem mit OpenCV Multi-Kamera-Triangulation,
 interaktiver 4-Punkt-Kalibrierung, 16 integrierten Dart-Spielen, 1 bis 6 Spielern
 und mehrsprachiger Oberfläche (Deutsch, Englisch, Französisch).
EOF

cat > "${STAGE_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q /usr/share/applications || true
fi
exit 0
EOF
chmod 0755 "${STAGE_DIR}/DEBIAN/postinst"

echo "[5/5] Baue .deb Archiv mit dpkg-deb..."
dpkg-deb --root-owner-group --build "${STAGE_DIR}" "${OUT_DEB}"
rm -rf "dist/deb_build"

echo "=================================================================="
echo "✅ FERTIG! Debian-Paket erstellt:"
ls -lh "${OUT_DEB}"
echo "   Installation mit: sudo dpkg -i ${OUT_DEB}"
echo "=================================================================="
