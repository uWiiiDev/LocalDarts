#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Erstelle Python Virtual Environment (.venv)..."
  python3 -m venv --without-pip .venv
  curl -sS https://bootstrap.pypa.io/get-pip.py | .venv/bin/python3
  .venv/bin/pip install -r requirements.txt
fi

echo "============================================================"
echo "🎯 LocalDarts Server startet auf http://localhost:8000"
echo "============================================================"
exec .venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
