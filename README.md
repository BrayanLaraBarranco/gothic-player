# 🎵 Music Player Pro — Gothic Edition v3.0

> Reproductor de audio y video con descarga automática de metadatos y miniaturas.  
> Tema **Gótico Victoriano** · Estilo Spotify (audio) + Netflix/YouTube (video)  
> Motor: **Kivy** — compatible con **APK Android** y **PC Windows/Linux/macOS**

---

## ✨ Características

| Función | Detalle |
|---|---|
| 🎵 Reproducción de audio | MP3, WAV, FLAC, M4A, AAC, OGG, OPUS |
| 🎬 Reproducción de video | MP4, AVI, MKV, MOV, WEBM, 3GP |
| ⬇️ Descarga con yt-dlp | YouTube, SoundCloud, y 1000+ sitios |
| 🖼️ Miniaturas automáticas | Incrustadas en el archivo MP3 (ID3 APIC) |
| 📋 Metadatos automáticos | Título, artista, álbum, duración en JSON sidecar |
| 📁 Gestión de biblioteca | Playlists, búsqueda, favoritos |
| 🎨 Diseño Gótico Victoriano | Paleta oscura, oro antiguo, carmesí |
| 📱 Android APK | via Buildozer + python-for-android |
| 💻 PC | Windows, Linux, macOS — lanzador incluido |

---

## 🚀 Ejecución en PC

### Windows

```bat
# Instalar dependencias
pip install -r requirements.txt

# También instalar:
# - VLC: https://www.videolan.org/vlc/
# - FFmpeg: https://ffmpeg.org/download.html  (agregar al PATH)

# Ejecutar
run_windows.bat
```

### Linux / macOS

```bash
pip3 install -r requirements.txt
chmod +x run_linux.sh
./run_linux.sh
```

### Directo con Python

```bash
python main.py
```

---

## 📦 Compilar APK para Android

### Requisitos previos (Linux/WSL2)

```bash
sudo apt update && sudo apt install -y \
    git zip unzip openjdk-17-jdk python3-pip \
    autoconf libtool pkg-config zlib1g-dev \
    libncurses5-dev libncursesw5-dev libtinfo5 \
    cmake libffi-dev libssl-dev

pip install buildozer cython
```

### Compilar

```bash
# Debug (para pruebas en dispositivo)
buildozer android debug

# Release (para distribución)
buildozer android release

# El APK aparece en: ./bin/
```

> ⏳ La **primera compilación** tarda 30-60 minutos porque descarga el Android SDK/NDK.  
> Las siguientes son mucho más rápidas (2-5 min).

### Instalar en dispositivo

```bash
# Con ADB:
adb install bin/musicplayergothic-3.0-arm64-v8a-debug.apk

# O copiar el APK al dispositivo y abrir con "Orígenes desconocidos" activado
```

---

## 📦 Generar EXE para Windows (PyInstaller)

```bash
pip install pyinstaller kivy_deps.sdl2 kivy_deps.glew
pyinstaller gothic_player.spec
# Resultado: dist/MusicPlayerGothic/MusicPlayerGothic.exe
```

---

## 🗂 Estructura del proyecto

```
gothic_player/
├── main.py                    # Punto de entrada Kivy
├── config.py                  # Configuración y tema de colores
├── requirements.txt           # Dependencias Python
├── buildozer.spec             # Configuración APK Android
├── gothic_player.spec         # Configuración EXE Windows
├── run_windows.bat            # Lanzador Windows
├── run_linux.sh               # Lanzador Linux/macOS
│
├── modules/
│   ├── player.py              # Backend audio (VLC / Kivy / Android)
│   ├── library.py             # Biblioteca de medios
│   ├── playlist_manager.py    # Gestión de playlists
│   ├── downloader.py          # Descargador yt-dlp
│   └── utils.py               # Utilidades
│
├── ui/
│   ├── theme.py               # Tema gótico + widgets base Kivy
│   ├── main_screen.py         # Pantalla principal + sidebar
│   ├── audio_player_widget.py # Widget reproductor de audio
│   ├── download_tab.py        # Pestaña de descargas
│   └── video_player.py        # Reproductor de video fullscreen
│
├── service/
│   └── player_service.py      # Servicio Android (audio en background)
│
└── assets/
    ├── icons/                 # Imágenes PNG de iconos
    └── fonts/                 # Fuentes TTF opcionales
```

---

## 🎨 Paleta de colores góticos

| Variable | Color | Uso |
|---|---|---|
| `bg` | `#0D0A0B` | Fondo principal |
| `accent` | `#6B1B2D` | Carmesí (botones activos) |
| `gold` | `#C9A961` | Dorado antiguo (títulos) |
| `gold_dark` | `#8B7340` | Dorado oscuro (bordes) |
| `text` | `#E8E0E4` | Texto principal |
| `text_secondary` | `#9A8A90` | Texto secundario |

---

## ⚠️ Notas importantes

- **VLC en Android**: No disponible. Se usa `android.media.MediaPlayer` nativo vía pyjnius.
- **FFmpeg**: Requerido para conversión de formatos. En Android, yt-dlp usa su propio binario.
- **Tkinter** (selector de archivos en PC): Incluido con Python estándar.  
  En Android se usa el `FileChooser` nativo de Kivy.
- **Permisos Android**: La app solicita acceso a almacenamiento e internet al instalarse.
- **Primer arranque**: Kivy compila shaders la primera vez; puede tardar 5-10 segundos extra.

---

## 🛠 Dependencias clave

```
kivy >= 2.3.0          # Motor gráfico multiplataforma
python-vlc >= 3.0      # Reproducción de audio/video en PC
yt-dlp >= 2024.1.1     # Descarga de contenido multimedia
mutagen >= 1.47        # Lectura/escritura de metadatos ID3
Pillow >= 10.0         # Procesamiento de imágenes/portadas
requests >= 2.31       # HTTP para thumbnails
```

---

*♦ Gothic Edition — Oscuridad refinada, música eterna ♦*
"# gothic-player-pro" 
