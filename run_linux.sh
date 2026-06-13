#!/usr/bin/env bash
# ══════════════════════════════════════════════════════
# Music Player Pro — Gothic Edition
# Lanzador para Linux / macOS
# ══════════════════════════════════════════════════════

set -e

echo ""
echo " ═══════════════════════════════════════════════"
echo "  ♫  MUSIC PLAYER PRO — GOTHIC EDITION v3.0"
echo " ═══════════════════════════════════════════════"
echo ""

# Verificar Python 3
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python 3 no encontrado."
    echo "Instala: sudo apt install python3  (Debian/Ubuntu)"
    echo "         brew install python3      (macOS)"
    exit 1
fi

# Verificar kivy
python3 -c "import kivy" 2>/dev/null || {
    echo "[INFO] Instalando dependencias..."
    pip3 install -r requirements.txt
}

# Lanzar
python3 main.py
