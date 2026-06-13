[app]

# ── Información ────────────────────────────────────────────────────────────────
title           = Gothic Player Pro
package.name    = gothicplayerpro
package.domain  = org.gothicplayer
version         = 3.0

# ── Fuentes ───────────────────────────────────────────────────────────────────
source.dir              = .
source.include_exts     = py,png,jpg,jpeg,webp,ttf,otf,json
source.include_patterns = assets/*,assets/**/*
source.exclude_dirs     = tests,bin,build,.git,__pycache__,.buildozer,venv,.venv
source.exclude_patterns = *.spec,*.pyc,*.pyo,*.bat,*.sh,*.zip,*.md

# ── Punto de entrada ──────────────────────────────────────────────────────────
entrypoint = main.py

# ── Orientación ───────────────────────────────────────────────────────────────
orientation = landscape

# ── Dependencias Python ───────────────────────────────────────────────────────
# Notas importantes:
# - python-vlc NO existe en p4a → se usa android.media via pyjnius
# - yt_dlp se escribe con guión bajo en pip pero yt-dlp en p4a
# - openssl → no se incluye directamente, viene con python3
# - ffpyplayer para reproducción de audio/video en Kivy
requirements = python3,kivy==2.3.0,pillow,mutagen,yt_dlp,requests,certifi,urllib3,charset-normalizer,idna,ffpyplayer,pyjnius

# ── Android SDK / NDK ─────────────────────────────────────────────────────────
android.minapi              = 24
android.api                 = 34
android.ndk                 = 25b
android.sdk                 = 34
android.archs               = arm64-v8a
android.enable_androidx     = True
android.accept_sdk_license  = True
android.build_tools_version = 34.0.0

# ── Permisos ──────────────────────────────────────────────────────────────────
android.permissions = \
    INTERNET,\
    READ_EXTERNAL_STORAGE,\
    WRITE_EXTERNAL_STORAGE,\
    READ_MEDIA_AUDIO,\
    READ_MEDIA_VIDEO,\
    READ_MEDIA_IMAGES,\
    FOREGROUND_SERVICE,\
    WAKE_LOCK

# ── Gradle ────────────────────────────────────────────────────────────────────
android.gradle_dependencies = androidx.multidex:multidex:2.0.1
android.add_gradle_repositories = google(),mavenCentral()

# ── Icono / Splash ────────────────────────────────────────────────────────────
# icon.filename      = assets/icons/icon.png
# presplash.filename = assets/icons/presplash.png
# presplash.color    = #0D0A0B

# ── Salida ────────────────────────────────────────────────────────────────────
android.release_artifact = apk
android.debug_artifact   = apk

# ── python-for-android ────────────────────────────────────────────────────────
p4a.branch = master

[buildozer]
log_level    = 2
warn_on_root = 1
build_dir    = .buildozer
bin_dir      = ./bin
