"""
Standalone Desktop Launcher for LocalDarts (Windows / Linux).
Starts the FastAPI/Uvicorn server and automatically opens the UI in the browser.
Used as the entry point for PyInstaller (LocalDarts.exe) and start_windows.bat.
"""

from __future__ import annotations
import os

# Suppress harmless OpenCV C++ VIDEOIO index probing warnings on Windows & Linux
os.environ["OPENCV_LOG_LEVEL"] = "OFF"
os.environ["OPENCV_VIDEOIO_DEBUG"] = "0"

import subprocess
import sys
import threading
import time
import webbrowser
import cv2

try:
    cv2.setLogLevel(0)
except Exception:
    pass

import uvicorn
from backend.main import app


def _open_ui(url: str) -> None:
    time.sleep(1.5)
    if sys.platform.startswith("win"):
        edge_paths = [
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        ]
        for edge in edge_paths:
            if os.path.exists(edge):
                try:
                    subprocess.Popen([edge, f"--app={url}", "--start-maximized"])
                    return
                except Exception:
                    pass
    webbrowser.open(url)


if __name__ == "__main__":
    port = int(os.environ.get("LOCALDARTS_PORT", "8000"))
    url = f"http://localhost:{port}"
    print("=" * 64)
    print(f"🎯 LocalDarts Server läuft auf: {url}")
    print("   Das Browser-/App-Fenster öffnet sich jetzt automatisch.")
    print("   (Falls nicht, öffne bitte http://localhost:8000 im Browser)")
    print("   Schließe dieses schwarze Fenster erst, wenn du fertig bist.")
    print("=" * 64)

    threading.Thread(target=_open_ui, args=(url,), daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
