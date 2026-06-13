@echo off
:: ══════════════════════════════════════════════════════
:: Music Player Pro — Gothic Edition
:: Lanzador para Windows
:: ══════════════════════════════════════════════════════

title Music Player Pro Gothic Edition

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no encontrado. Instala Python 3.10 o superior.
    echo Descarga: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Verificar dependencias y ofrecer instalación
echo Verificando dependencias...
python -c "import kivy" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando dependencias (primera vez, puede tardar varios minutos)...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Fallo la instalacion de dependencias.
        pause
        exit /b 1
    )
)

:: Verificar backend de video
python -c "import ffpyplayer" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando backend de video (ffpyplayer)...
    pip install ffpyplayer
)

:: Iniciar app
echo.
echo  ═══════════════════════════════════════════════
echo   ♫  MUSIC PLAYER PRO — GOTHIC EDITION v3.0
echo  ═══════════════════════════════════════════════
echo.
python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] La aplicacion termino con un error.
    pause
)
