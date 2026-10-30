#!/usr/bin/env bash
# Baut direkt unter Linux ein komplett fertiges Offline-Windows-Paket
# inklusive eingebettetem lokalem Windows-Python (python_embed) und allen
# vorinstallierten Windows-Bibliotheken (OpenCV, FastAPI, NumPy, Uvicorn).
set -e
cd "$(dirname "$0")"

PY_VER="3.12.8"
PY_ZIP="python-${PY_VER}-embed-amd64.zip"
PY_URL="https://www.python.org/ftp/python/${PY_VER}/${PY_ZIP}"
DIST_DIR="dist/LocalDarts-Windows"
EMBED_DIR="${DIST_DIR}/python_embed"
WHEELS_DIR="dist/win_wheels"

echo "=================================================================="
echo "📦 Erstelle komplettes Windows-Paket inkl. lokalem Python (${PY_VER})"
echo "=================================================================="

rm -rf "${DIST_DIR}" "${WHEELS_DIR}"
mkdir -p "${EMBED_DIR}" "${WHEELS_DIR}/site-packages" "${DIST_DIR}/config"

echo "[1/4] Lade offizielles portables Windows-Python (${PY_VER} 64-bit) herunter..."
curl -sSL "${PY_URL}" -o "dist/${PY_ZIP}"
python3 -m zipfile -e "dist/${PY_ZIP}" "${EMBED_DIR}"
rm -f "dist/${PY_ZIP}"

# Konfiguriere python312._pth so, dass Lib/site-packages und das Projektverzeichnis geladen werden
cat > "${EMBED_DIR}/python312._pth" << 'EOF'
python312.zip
.
..
Lib/site-packages
import site
EOF

echo "[2/4] Lade vorkompilierte Windows-64-Bit-Pakete (.whl) herunter..."
.venv/bin/pip download \
  --platform win_amd64 \
  --python-version 312 \
  --implementation cp \
  --abi cp312 \
  --only-binary=:all: \
  --dest "${WHEELS_DIR}" \
  fastapi uvicorn opencv-python-headless numpy websockets pydantic

echo "[3/4] Entpacke Windows-Pakete direkt in python_embed/Lib/site-packages..."
mkdir -p "${EMBED_DIR}/Lib/site-packages"
for whl in "${WHEELS_DIR}"/*.whl; do
  python3 -m zipfile -e "${whl}" "${EMBED_DIR}/Lib/site-packages"
done
rm -rf "${WHEELS_DIR}"

echo "[4/4] Kopiere LocalDarts Anwendungsdateien und schnüre ZIP-Paket..."
cp -r backend frontend run_app.py requirements.txt start_windows.bat installer_windows.iss "${DIST_DIR}/"

python3 - << 'PYEOF'
import shutil
shutil.make_archive("dist/LocalDarts-Windows-Full-Offline", "zip", "dist", "LocalDarts-Windows")
PYEOF

echo "=================================================================="
echo "✅ FERTIG! Komplettes Offline-Windows-Paket inkl. lokalem Python:"
echo "   📁 Ordner: dist/LocalDarts-Windows/"
echo "   🗜️ ZIP:    dist/LocalDarts-Windows-Full-Offline.zip"
echo "=================================================================="
