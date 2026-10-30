"""
Standalone Desktop Launcher for LocalDarts (Windows / Linux).
Starts the FastAPI/Uvicorn server and automatically opens the UI in the browser.
Used as the entry point for PyInstaller (LocalDarts.exe).
"""

from __future__ import annotations
import os
import subprocess
import sys
import threading
import time
import webbrowser
import uvicorn

from backend.main import app


def _open_ui(url: str) -> None:
    time.sleep(1.2)
    if sys.platform.startswith("win"):
        # Try opening Microsoft Edge in native App-Window mode first (looks like a native desktop app)
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
    print("=" * 62)
    print(f"🎯 LocalDarts Server startet auf {url}")
    print("   Schließe dieses Fenster, um LocalDarts zu beenden.")
    print("=" * 62)

    threading.Thread(target=_open_ui, args=(url,), daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
