@echo off
:: ══════════════════════════════════════════════════════
:: Instalar soporte de video para Gothic Player Pro
:: Ejecutar UNA VEZ antes de usar el reproductor de video
:: ══════════════════════════════════════════════════════
echo.
echo  Instalando soporte de video (ffpyplayer)...
echo.

python -m pip install ffpyplayer

if %errorlevel% == 0 (
    echo.
    echo  OK - Soporte de video instalado correctamente.
    echo  Ahora puedes reproducir MP4, MKV, AVI, etc.
) else (
    echo.
    echo  ERROR al instalar. Intenta manualmente:
    echo    pip install ffpyplayer
)
echo.
pause
