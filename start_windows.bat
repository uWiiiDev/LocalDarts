@echo off
chcp 65001 >nul
title LocalDarts - Lokales Autodarts System
cd /d "%~dp0"

REM 1. Pruefe zuerst auf das mitgelieferte lokale Embedded-Python (kein installiertes Python noetig!)
if exist "python_embed\python.exe" (
    echo [LocalDarts] Starte mit integriertem lokalem Python ^(python_embed^)...
    "python_embed\python.exe" run_app.py
    pause
    exit /b 0
)

REM 2. Fallback: Falls kein python_embed Ordner vorhanden ist, lade Embedded Python automatisch herunter
if not exist ".venv\Scripts\python.exe" (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        echo [1/2] Erstelle virtuelle Python-Umgebung ^(.venv^)...
        python -m venv .venv
        echo [2/2] Installiere Abhaengigkeiten...
        .venv\Scripts\pip install --upgrade pip
        .venv\Scripts\pip install -r requirements.txt
    ) else (
        echo [1/3] Kein Python installiert - lade portables lokales Python 3.12 fuer Windows herunter...
        mkdir python_embed 2>nul
        powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip' -OutFile 'python_embed\py.zip'"
        powershell -Command "Expand-Archive -Path 'python_embed\py.zip' -DestinationPath 'python_embed' -Force"
        del "python_embed\py.zip"
        echo python312.zip> "python_embed\python312._pth"
        echo .>> "python_embed\python312._pth"
        echo ..>> "python_embed\python312._pth"
        echo Lib\site-packages>> "python_embed\python312._pth"
        echo import site>> "python_embed\python312._pth"
        echo [2/3] Richte pip im lokalen Python ein...
        powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'python_embed\get-pip.py'"
        "python_embed\python.exe" "python_embed\get-pip.py" --no-warn-script-location
        echo [3/3] Installiere Pakete in python_embed...
        "python_embed\python.exe" -m pip install -r requirements.txt --no-warn-script-location
        "python_embed\python.exe" run_app.py
        pause
        exit /b 0
    )
)

echo Starte LocalDarts...
.venv\Scripts\python.exe run_app.py
pause
