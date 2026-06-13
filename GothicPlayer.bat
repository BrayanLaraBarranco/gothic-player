@echo off
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo ERROR: Revisa que Python y Kivy estén instalados.
    echo   pip install kivy ffpyplayer
    pause
)
