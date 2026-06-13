"""
Configuración del reproductor — Tema Gótico Victoriano
Compatible con Android y escritorio
"""
import os
import json
from pathlib import Path
from kivy.utils import platform

# ── Carpetas base ──────────────────────────────────────────────────────────────
if platform == 'android':
    from android.storage import app_storage_path, primary_external_storage_path  # type: ignore
    try:
        _BASE = Path(primary_external_storage_path()) / 'MusicPlayerGothic'
    except Exception:
        _BASE = Path(app_storage_path()) / 'MusicPlayerGothic'
else:
    _BASE = Path.home() / 'MusicPlayerGothic'

APP_FOLDER      = _BASE
DOWNLOADS_FOLDER = _BASE / 'Downloads'
COVERS_FOLDER   = _BASE / 'Covers'
PLAYLISTS_FOLDER = _BASE / 'Playlists'
PLAYLIST_FILE   = _BASE / 'library.json'
CONFIG_FILE     = _BASE / 'config.json'

for _d in [APP_FOLDER, DOWNLOADS_FOLDER, COVERS_FOLDER, PLAYLISTS_FOLDER]:
    _d.mkdir(parents=True, exist_ok=True)

# ── Extensiones ────────────────────────────────────────────────────────────────
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.opus'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.webm', '.3gp'}

# ── Dimensiones ventana escritorio ────────────────────────────────────────────
WINDOW_WIDTH  = 1400
WINDOW_HEIGHT = 850
MIN_WIDTH     = 800
MIN_HEIGHT    = 600

# ── Paleta Gótico Victoriano ──────────────────────────────────────────────────
GOTHIC_THEME = {
    # Fondos
    'bg':              '#0D0A0B',
    'bg_secondary':    '#1A1418',
    'surface':         '#1E1820',
    'surface_light':   '#2A2228',
    'surface_hover':   '#3A2F35',

    # Carmesí
    'accent':          '#6B1B2D',
    'accent_hover':    '#8B2540',
    'accent_light':    '#A03050',

    # Dorados
    'gold':            '#C9A961',
    'gold_dark':       '#8B7340',
    'gold_light':      '#E6C847',
    'gold_muted':      '#6B5A1E',
    'bronze':          '#8B6914',

    # Texto
    'text':            '#E8E0E4',
    'text_secondary':  '#9A8A90',
    'text_muted':      '#5A4A50',

    # Estados
    'success':         '#2D5A3D',
    'error':           '#6B1B2D',
    'warning':         '#8B6914',

    # Bordes
    'border':          '#3A2A30',
    'border_light':    '#5A4A50',
    'border_gold':     '#8B7340',

    # Seekbar
    'seekbar_bg':      '#2A2228',
    'seekbar_fill':    '#8B1538',
    'seekbar_thumb':   '#C9A961',
}

CURRENT_THEME = GOTHIC_THEME

# ── Helpers de color Kivy (RGBA 0-1) ──────────────────────────────────────────
def hex_to_rgba(hex_color: str, alpha: float = 1.0):
    """Convierte #RRGGBB → (r, g, b, a) en rango 0-1 para Kivy"""
    h = hex_color.lstrip('#')
    r = int(h[0:2], 16) / 255
    g = int(h[2:4], 16) / 255
    b = int(h[4:6], 16) / 255
    return (r, g, b, alpha)

def theme_rgba(key: str, alpha: float = 1.0):
    return hex_to_rgba(GOTHIC_THEME.get(key, '#000000'), alpha)


# ── Configuración persistente ─────────────────────────────────────────────────
class AppConfig:
    def __init__(self):
        self._data = self._load()

    def _load(self):
        defaults = {
            'downloads_folder': str(DOWNLOADS_FOLDER),
            'volume': 70,
            'last_playlist': 'Mi Biblioteca',
            'shuffle_enabled': False,
            'repeat_mode': 0,
        }
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                defaults.update(saved)
        except Exception:
            pass
        return defaults

    def save(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f'[Config] Error al guardar: {e}')

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()

    def get_downloads_folder(self) -> Path:
        folder = Path(self._data.get('downloads_folder', str(DOWNLOADS_FOLDER)))
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def set_downloads_folder(self, folder: str):
        self._data['downloads_folder'] = folder
        self.save()

    def apply_saved_theme(self):
        """Aplica los colores y la imagen de fondo guardados al ThemeManager."""
        try:
            from ui.theme import theme as _theme
            acc  = self._data.get('accent_color')
            gold = self._data.get('gold_color')
            bg   = self._data.get('bg_color')
            surf = self._data.get('surface_color')
            img  = self._data.get('bg_image', '')
            op   = self._data.get('bg_opacity', 0.18)
            if acc:  _theme.set_accent(acc)
            if gold: _theme.set_gold(gold)
            if bg:   _theme.set_bg(bg)
            if surf: _theme.set_surface(surf)
            if img:  _theme.set_bg_image(img, opacity=op)
        except Exception as e:
            print(f'[Config] apply_saved_theme: {e}')


# Instancia global
app_config = AppConfig()
