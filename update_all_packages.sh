#!/usr/bin/env bash
# Aktualisiert sowohl das Windows-Offline-Paket (ZIP) als auch das Linux-Debian-Paket (.deb)
# und lädt beide automatisch in das GitHub-Release v1.0.0 hoch.
set -e
cd "$(dirname "$0")"

echo "🔄 [1/3] Aktualisiere Windows-Offline-Paket (dist/LocalDarts-Windows-Full-Offline.zip)..."
if [ -d "dist/LocalDarts-Windows/python_embed" ]; then
  # Schnelles Update der Anwendungsdateien ohne erneuten Download von Python & Wheels
  cp -r backend frontend run_app.py requirements.txt start_windows.bat installer_windows.iss README.md dist/LocalDarts-Windows/
  python3 -c "import shutil; shutil.make_archive('dist/LocalDarts-Windows-Full-Offline', 'zip', 'dist', 'LocalDarts-Windows')"
else
  ./build_windows_bundle_on_linux.sh
fi

echo "🔄 [2/3] Aktualisiere Linux Debian-Paket (dist/localdarts_1.0.0_amd64.deb)..."
./build_deb.sh

echo "🚀 [3/3] Lade beide Pakete ins GitHub-Release v1.0.0 hoch..."
if /home/uwe/.local/bin/gh release view v1.0.0 >/dev/null 2>&1; then
  /home/uwe/.local/bin/gh release upload v1.0.0 \
    dist/LocalDarts-Windows-Full-Offline.zip \
    dist/localdarts_1.0.0_amd64.deb \
    --clobber
  echo "✅ Beide Pakete (Windows ZIP + Linux DEB) auf GitHub aktualisiert!"
else
  echo "ℹ️ Lokale Pakete unter dist/ aktualisiert."
fi
