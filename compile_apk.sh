#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
#  Gothic Player Pro — Script de compilación APK
#  Compatible con: Ubuntu 22.04 nativo · WSL2 en Windows
#  Uso:  chmod +x compile_apk.sh && ./compile_apk.sh
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo -e "${GREEN}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║     Gothic Player Pro — APK Builder          ║"
echo "  ║     Ubuntu 22.04 / WSL2 ready                ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Verificar que estamos en Linux ─────────────────────────────────────────
echo -e "${YELLOW}[1/6] Verificando sistema...${NC}"
if [[ "$(uname -s)" != "Linux" ]]; then
    echo -e "${RED}ERROR: Este script requiere Linux o WSL2 (Ubuntu 22.04).${NC}"
    echo "  En Windows: wsl --install -d Ubuntu-22.04"
    exit 1
fi

# Detectar si estamos en WSL2
if grep -qi microsoft /proc/version 2>/dev/null; then
    echo -e "${CYAN}  → Detectado: WSL2${NC}"
else
    echo -e "${CYAN}  → Detectado: Linux nativo${NC}"
fi

python3 --version || { echo -e "${RED}Python3 no encontrado${NC}"; exit 1; }
echo -e "${GREEN}  ✓ Sistema OK${NC}"

# ── 2. Instalar dependencias del sistema ──────────────────────────────────────
echo -e "${YELLOW}[2/6] Instalando dependencias del sistema...${NC}"
sudo apt-get update -qq
sudo apt-get install -y -qq \
    git zip unzip wget curl \
    openjdk-17-jdk \
    python3-pip python3-venv \
    autoconf libtool pkg-config \
    zlib1g-dev libncurses5-dev libncursesw5-dev \
    cmake libffi-dev libssl-dev \
    libjpeg-dev libpng-dev \
    build-essential lld
echo -e "${GREEN}  ✓ Dependencias del sistema instaladas${NC}"

# ── 3. Configurar JAVA_HOME ───────────────────────────────────────────────────
echo -e "${YELLOW}[3/6] Configurando Java...${NC}"
JAVA_BIN=$(readlink -f "$(which java)")
export JAVA_HOME
JAVA_HOME=$(dirname "$(dirname "$JAVA_BIN")")
echo "  JAVA_HOME = $JAVA_HOME"
java -version 2>&1 | head -1

# Persistir JAVA_HOME en ~/.bashrc si no está ya
if ! grep -q "JAVA_HOME" ~/.bashrc 2>/dev/null; then
    echo "export JAVA_HOME=$JAVA_HOME" >> ~/.bashrc
    echo "  → JAVA_HOME guardado en ~/.bashrc"
fi
echo -e "${GREEN}  ✓ Java configurado${NC}"

# ── 4. Instalar buildozer y Cython ────────────────────────────────────────────
echo -e "${YELLOW}[4/6] Instalando buildozer y Cython...${NC}"
pip3 install --upgrade pip --quiet

# Ubuntu 22.04+ puede requerir --break-system-packages
if pip3 install buildozer cython --quiet 2>/dev/null; then
    echo -e "${GREEN}  ✓ Instalado correctamente${NC}"
elif pip3 install buildozer cython --break-system-packages --quiet; then
    echo -e "${GREEN}  ✓ Instalado con --break-system-packages${NC}"
else
    echo -e "${RED}  ERROR: No se pudo instalar buildozer.${NC}"
    echo "  Intenta manualmente: pip3 install buildozer cython --break-system-packages"
    exit 1
fi

BUILDOZER_VERSION=$(buildozer --version 2>&1 | head -1 || echo "desconocida")
echo "  Buildozer: $BUILDOZER_VERSION"

# ── 5. Verificar buildozer.spec ───────────────────────────────────────────────
echo -e "${YELLOW}[5/6] Verificando proyecto...${NC}"
if [ ! -f "buildozer.spec" ]; then
    echo -e "${RED}ERROR: No se encontró buildozer.spec en el directorio actual.${NC}"
    echo "  Asegúrate de ejecutar este script DENTRO de la carpeta gothic_player/"
    echo "  Ejemplo: cd ~/gothic_player && ./compile_apk.sh"
    exit 1
fi
echo -e "${GREEN}  ✓ buildozer.spec encontrado${NC}"

# ── 6. Compilar APK ───────────────────────────────────────────────────────────
echo -e "${YELLOW}[6/6] Compilando APK...${NC}"
echo ""
echo -e "${YELLOW}  NOTA: La primera compilación descarga ~2 GB (SDK, NDK)."
echo -e "  Tiempo estimado: 30-60 min la primera vez, 3-8 min las siguientes.${NC}"
echo ""

# Preguntar si limpiar compilación anterior
if [ -d ".buildozer" ]; then
    read -rp "  ¿Limpiar compilación anterior? (recomendado si hubo errores) [s/N]: " clean
    if [[ "$clean" =~ ^[Ss]$ ]]; then
        echo "  Limpiando..."
        buildozer android clean
    fi
fi

# Compilar y guardar log
buildozer -v android debug 2>&1 | tee build.log

# ── Resultado ─────────────────────────────────────────────────────────────────
if ls bin/*.apk 1>/dev/null 2>&1; then
    APK=$(ls bin/*.apk | head -1)
    SIZE=$(du -h "$APK" | cut -f1)
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ APK COMPILADO EXITOSAMENTE                    ║${NC}"
    echo -e "${GREEN}║                                                  ║${NC}"
    printf "${GREEN}║  Archivo: %-38s ║${NC}\n" "$APK"
    printf "${GREEN}║  Tamaño:  %-38s ║${NC}\n" "$SIZE"
    echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  Para instalar en Android (con USB):"
    echo "    sudo apt install android-tools-adb"
    echo "    adb install $APK"
    echo ""
    echo "  O copia el APK a tu dispositivo y abre con"
    echo "  'Instalar desde fuentes desconocidas' activado."
else
    echo ""
    echo -e "${RED}✗ La compilación falló. Revisa build.log${NC}"
    echo ""
    echo "  Errores más comunes:"
    echo "    - Error de red al descargar SDK/NDK → vuelve a ejecutar el script"
    echo "    - Sin espacio en disco             → buildozer android clean"
    echo "    - Java no encontrado               → sudo apt install openjdk-17-jdk"
    echo "    - pip externally-managed           → ya manejado automáticamente"
    echo ""
    echo "  Últimas líneas del log:"
    tail -20 build.log
    exit 1
fi
