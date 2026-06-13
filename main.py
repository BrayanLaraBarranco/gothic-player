"""
Gothic Player Pro — Motor Kivy
Compatible con APK Android y Windows/Linux/macOS
"""
import os
import sys

# ── Asegurar que la raíz del proyecto esté en sys.path ───────────────────────
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

# ── Variables de entorno ANTES de importar kivy ───────────────────────────────
os.environ.setdefault('KIVY_NO_ENV_CONFIG', '1')
os.environ['KIVY_VIDEO'] = 'ffpyplayer'

from kivy.config import Config
Config.set('graphics', 'resizable', '1')
Config.set('kivy',     'log_level', 'warning')
Config.set('input',    'mouse',     'mouse,multitouch_on_demand')

from kivy.app         import App
from kivy.core.window import Window
from kivy.utils       import platform

# ── Tamaño ventana escritorio ─────────────────────────────────────────────────
if platform not in ('android', 'ios'):
    Window.size = (1400, 850)
    try:
        Window.minimum_size = (800, 600)
    except AttributeError:
        Window.minimum_width  = 800
        Window.minimum_height = 600

# ── Android: permisos en tiempo de ejecución (Android 6+) ────────────────────
if platform == 'android':
    try:
        from android.permissions import (
            request_permissions, Permission)
        request_permissions([
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.INTERNET,
        ])
    except Exception:
        pass

    # Habilitar lectura de medios en Android 13+
    try:
        from android.permissions import Permission
        request_permissions([
            Permission.READ_MEDIA_AUDIO,
            Permission.READ_MEDIA_VIDEO,
            Permission.READ_MEDIA_IMAGES,
        ])
    except Exception:
        pass

# ── ffpyplayer: aviso amigable en escritorio si no está instalado ─────────────
if platform not in ('android', 'ios'):
    try:
        import ffpyplayer  # noqa
    except ImportError:
        print(
            "\n[Gothic Player] AVISO: ffpyplayer no instalado.\n"
            "  Instálalo con:  pip install ffpyplayer\n"
        )

from ui.main_screen import MainScreen


class GothicPlayerApp(App):
    title = "Gothic Player Pro"

    def build(self):
        from config import app_config
        app_config.apply_saved_theme()
        self._register_fonts()
        return MainScreen()

    def _register_fonts(self):
        try:
            from kivy.core.text import LabelBase
            assets = os.path.join(_ROOT, 'assets', 'fonts')
            if os.path.isdir(assets):
                for fn in os.listdir(assets):
                    if fn.endswith(('.ttf', '.otf')):
                        name = os.path.splitext(fn)[0]
                        LabelBase.register(name, os.path.join(assets, fn))
        except Exception:
            pass

    def on_pause(self):  return True
    def on_resume(self): pass


if __name__ == '__main__':
    GothicPlayerApp().run()
