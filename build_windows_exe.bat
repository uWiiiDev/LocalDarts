@echo off
chcp 65001 >nul
title LocalDarts - Windows EXE & Installer Builder
cd /d "%~dp0"

echo =====================================================================
echo 🎯 LocalDarts Windows Paket-Erstellung (PyInstaller)
echo =====================================================================

if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Erstelle virtuelle Python-Umgebung...
    python -m venv .venv
)

echo [2/4] Installiere Abhaengigkeiten + PyInstaller...
.venv\Scripts\pip install --upgrade pip
.venv\Scripts\pip install -r requirements.txt pyinstaller

echo [3/4] Kompiliere eigenstaendige LocalDarts.exe (ohne Python-Zwang)...
.venv\Scripts\pyinstaller --noconfirm --clean ^
    --name "LocalDarts" ^
    --onedir ^
    --console ^
    --add-data "frontend;frontend" ^
    --hidden-import "uvicorn.logging" ^
    --hidden-import "uvicorn.loops" ^
    --hidden-import "uvicorn.loops.auto" ^
    --hidden-import "uvicorn.protocols" ^
    --hidden-import "uvicorn.protocols.http" ^
    --hidden-import "uvicorn.protocols.http.auto" ^
    --hidden-import "uvicorn.protocols.websockets" ^
    --hidden-import "uvicorn.protocols.websockets.auto" ^
    --hidden-import "uvicorn.lifespan" ^
    --hidden-import "uvicorn.lifespan.on" ^
    run_app.py

echo [4/4] Erstelle ZIP-Paket dist\LocalDarts-Windows-Portable.zip ...
powershell -Command "Compress-Archive -Path 'dist\LocalDarts\*' -DestinationPath 'dist\LocalDarts-Windows-Portable.zip' -Force"

echo.
echo =====================================================================
echo ✅ FERTIG!
echo   - Ausfuehrbares Programm: dist\LocalDarts\LocalDarts.exe
echo   - Portables ZIP-Archiv:   dist\LocalDarts-Windows-Portable.zip
echo   - Optional: Oeffne 'installer_windows.iss' mit Inno Setup, um
echo     eine klassische 'LocalDarts-Setup.exe' mit Desktop-Icon zu bauen!
echo =====================================================================
pause
