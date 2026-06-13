# ══════════════════════════════════════════════════════════════════════════════
# gothic_player.spec  —  PyInstaller para Windows EXE
# Uso: pyinstaller gothic_player.spec
# ══════════════════════════════════════════════════════════════════════════════
import sys
import os
from pathlib import Path
from kivy_deps import sdl2, glew  # pip install kivy_deps.sdl2 kivy_deps.glew

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(Path.cwd())],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('modules', 'modules'),
        ('ui', 'ui'),
        ('config.py', '.'),
    ],
    hiddenimports=[
        'kivy',
        'kivy.core.window',
        'kivy.core.audio',
        'kivy.core.audio.audio_sdl2',
        'kivy.core.video',
        'kivy.core.video.video_ffpyplayer',
        'kivy.uix.video',
        'mutagen',
        'mutagen.mp3',
        'mutagen.id3',
        'yt_dlp',
        'PIL',
        'PIL.Image',
        'requests',
        'certifi',
        'charset_normalizer',
        'idna',
        'urllib3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter._test', 'test', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MusicPlayerGothic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # Sin ventana de consola
    # icon='assets/icons/icon.ico',   # Descomenta si tienes icono .ico
)

coll = COLLECT(
    exe,
    Tree('./assets', prefix='assets'),
    a.binaries,
    a.zipfiles,
    a.datas,
    *[Tree(p) for p in sdl2.dep_bins + glew.dep_bins],
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MusicPlayerGothic',
)

# ── INSTRUCCIONES ─────────────────────────────────────────────────────────────
# 1. pip install pyinstaller kivy_deps.sdl2 kivy_deps.glew
# 2. pyinstaller gothic_player.spec
# 3. El ejecutable estará en: dist/MusicPlayerGothic/MusicPlayerGothic.exe
# 4. Para distribuir, comprime toda la carpeta dist/MusicPlayerGothic/
# ──────────────────────────────────────────────────────────────────────────────
