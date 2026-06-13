"""
Tema Gótico Victoriano — Kivy
ThemeManager centralizado: gestiona colores Y imagen de fondo en tiempo real.
Todos los widgets se registran y se actualizan sin reiniciar la app.
"""
import os
from kivy.uix.widget     import Widget
from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors  import ButtonBehavior
from kivy.graphics import (Color, Rectangle, RoundedRectangle, Line, Ellipse)
from kivy.properties import (NumericProperty, BooleanProperty,
                              ListProperty, ObjectProperty)
from kivy.metrics import dp, sp
from config import hex_to_rgba, GOTHIC_THEME as T


# ══════════════════════════════════════════════════════════════════════════════
#  ThemeManager — singleton centralizado
# ══════════════════════════════════════════════════════════════════════════════
class ThemeManager:
    """
    Singleton que gestiona:
      - Todos los colores del tema (accent, gold, bg, surface, text…)
      - Imagen de fondo global (ruta + opacidad)
    Los widgets se registran con .register_widget(w) y reciben on_theme_update()
    cuando cambia algo.  También hay registro de Color-objects individuales para
    actualizaciones quirúrgicas sin redibujar toda la vista.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            inst = super().__new__(cls)
            inst._colors = dict(T)           # copia mutable de toda la paleta
            inst._bg_image   = ''            # ruta a la imagen de fondo
            inst._bg_opacity = 0.18          # opacidad de la imagen (0-1)
            inst._color_refs  = []           # [(Color_obj, role), ...]
            inst._widgets     = []           # [widget_ref, ...]  on_theme_update
            cls._instance = inst
        return cls._instance

    # ── Lectura de colores ────────────────────────────────────────────────────
    def get(self, key, alpha=1.0):
        """Devuelve (r,g,b,a) del color con nombre key."""
        return hex_to_rgba(self._colors.get(key, '#000000'), alpha)

    def get_hex(self, key):
        return self._colors.get(key, '#000000')

    # Atajos de uso frecuente
    @property
    def accent(self):       return self.get('accent')
    @property
    def accent_hover(self):
        h = self._colors['accent'].lstrip('#')
        r = min(255, int(h[0:2], 16) + 30)
        g = min(255, int(h[2:4], 16) + 10)
        b = min(255, int(h[4:6], 16) + 10)
        return (r/255, g/255, b/255, 1.0)
    @property
    def gold(self):         return self.get('gold')
    @property
    def gold_dark(self):
        h = self._colors['gold'].lstrip('#')
        r = max(0, int(h[0:2], 16) - 40)
        g = max(0, int(h[2:4], 16) - 35)
        b = max(0, int(h[4:6], 16) - 20)
        return (r/255, g/255, b/255, 1.0)
    @property
    def gold_muted(self):
        g = self.gold
        return (g[0]*0.6, g[1]*0.6, g[2]*0.6, 1.0)
    @property
    def bg(self):           return self.get('bg')
    @property
    def bg2(self):          return self.get('bg_secondary')
    @property
    def surface(self):      return self.get('surface')
    @property
    def surface_light(self):return self.get('surface_light')
    @property
    def text(self):         return self.get('text')
    @property
    def text_sec(self):     return self.get('text_secondary')
    @property
    def text_muted(self):   return self.get('text_muted')
    @property
    def border(self):       return self.get('border')
    @property
    def border_gold(self):  return self.get('border_gold')

    # ── Imagen de fondo ───────────────────────────────────────────────────────
    @property
    def bg_image(self):    return self._bg_image
    @property
    def bg_opacity(self):  return self._bg_opacity

    def set_bg_image(self, path, opacity=None):
        self._bg_image = path or ''
        if opacity is not None:
            self._bg_opacity = max(0.0, min(1.0, opacity))
        self._notify_all()

    def set_bg_opacity(self, opacity):
        self._bg_opacity = max(0.0, min(1.0, opacity))
        self._notify_all()

    def clear_bg_image(self):
        self._bg_image = ''
        self._notify_all()

    # ── Setters de color ──────────────────────────────────────────────────────
    def set_color(self, key, hex_color):
        """Cambia cualquier color del tema por clave y notifica a todos."""
        self._colors[key] = hex_color
        # Sincronizar aliases
        if key == 'accent':
            self._colors['accent_hover'] = hex_color  # se recalcula en propiedad
            self._colors['seekbar_fill'] = hex_color
        elif key == 'gold':
            self._colors['seekbar_thumb'] = hex_color
        self._notify_color_refs(key)
        self._notify_all()
        # Actualizar constantes globales de este módulo
        _sync_globals()

    def set_accent(self, hex_color):  self.set_color('accent', hex_color)
    def set_gold(self, hex_color):    self.set_color('gold', hex_color)
    def set_bg(self, hex_color):      self.set_color('bg', hex_color)
    def set_bg2(self, hex_color):     self.set_color('bg_secondary', hex_color)
    def set_surface(self, hex_color): self.set_color('surface', hex_color)

    # ── Registro de widgets ───────────────────────────────────────────────────
    def register_widget(self, widget):
        """
        Registra un widget para recibir on_theme_update() cuando cambia el tema.
        El widget debe implementar on_theme_update(self).
        """
        import weakref
        self._widgets.append(weakref.ref(widget))

    def register(self, color_obj, role):
        """Registra un objeto Color de kivy para actualización directa."""
        self._color_refs.append((color_obj, role))

    # ── Notificación ─────────────────────────────────────────────────────────
    def _notify_color_refs(self, changed_key):
        dead = []
        for ref in self._color_refs:
            color_obj, role = ref
            try:
                new_rgba = None
                if role == 'accent':       new_rgba = self.accent
                elif role == 'accent_hover': new_rgba = self.accent_hover
                elif role == 'gold':       new_rgba = self.gold
                elif role == 'gold_dark':  new_rgba = self.gold_dark
                elif role == 'gold_muted': new_rgba = self.gold_muted
                elif role == 'bg':         new_rgba = self.bg
                elif role == 'bg2':        new_rgba = self.bg2
                elif role == 'surface':    new_rgba = self.surface
                elif role == 'text':       new_rgba = self.text
                elif role == 'text_sec':   new_rgba = self.text_sec
                if new_rgba:
                    color_obj.rgba = list(new_rgba)
            except Exception:
                dead.append(ref)
        for d in dead:
            try: self._color_refs.remove(d)
            except ValueError: pass

    def _notify_all(self):
        """Llama on_theme_update() en todos los widgets registrados."""
        _sync_globals()
        dead = []
        for ref in self._widgets:
            try:
                w = ref()
                if w is None:
                    dead.append(ref)
                elif hasattr(w, 'on_theme_update'):
                    w.on_theme_update()
            except Exception:
                dead.append(ref)
        for d in dead:
            try: self._widgets.remove(d)
            except ValueError: pass

    def apply_full(self):
        self._notify_color_refs('accent')
        self._notify_color_refs('gold')
        self._notify_all()


# Instancia global
theme = ThemeManager()


# ── Constantes de color (se sincronizan con ThemeManager) ────────────────────
def _sync_globals():
    """Actualiza las constantes C_* de este módulo desde ThemeManager."""
    import ui.theme as _m
    _m.C_BG         = theme.bg
    _m.C_BG2        = theme.bg2
    _m.C_SURFACE    = theme.surface
    _m.C_SURFACE_L  = theme.get('surface_light')
    _m.C_SURFACE_H  = theme.get('surface_hover')
    _m.C_ACCENT     = theme.accent
    _m.C_ACCENT_H   = theme.accent_hover
    _m.C_GOLD       = theme.gold
    _m.C_GOLD_D     = theme.gold_dark
    _m.C_GOLD_M     = theme.gold_muted
    _m.C_TEXT       = theme.text
    _m.C_TEXT_SEC   = theme.text_sec
    _m.C_TEXT_MUT   = theme.text_muted
    _m.C_BORDER     = theme.border
    _m.C_BORDER_G   = theme.border_gold
    _m.C_SEEK_BG    = theme.get('seekbar_bg')
    _m.C_SEEK_FILL  = theme.accent
    _m.C_SEEK_THUMB = theme.gold


C_BG         = theme.bg
C_BG2        = theme.bg2
C_SURFACE    = theme.surface
C_SURFACE_L  = theme.get('surface_light')
C_SURFACE_H  = theme.get('surface_hover')
C_ACCENT     = theme.accent
C_ACCENT_H   = theme.accent_hover
C_GOLD       = theme.gold
C_GOLD_D     = theme.gold_dark
C_GOLD_M     = theme.gold_muted
C_TEXT       = theme.text
C_TEXT_SEC   = theme.text_sec
C_TEXT_MUT   = theme.text_muted
C_BORDER     = theme.border
C_BORDER_G   = theme.border_gold
C_SEEK_BG    = theme.get('seekbar_bg')
C_SEEK_FILL  = theme.accent
C_SEEK_THUMB = theme.gold
C_TRANS      = (0, 0, 0, 0)


# ── draw_bg helper ────────────────────────────────────────────────────────────
def draw_bg(widget, color, radius=0, border_color=None, border_w=1.2):
    """Dibuja fondo en canvas.before sincronizado con pos/size."""
    refs = {}
    with widget.canvas.before:
        Color(*color)
        if radius:
            refs['bg'] = RoundedRectangle(pos=widget.pos, size=widget.size,
                                          radius=[radius])
        else:
            refs['bg'] = Rectangle(pos=widget.pos, size=widget.size)
        if border_color:
            Color(*border_color)
            refs['bd'] = Line(
                rounded_rectangle=(*widget.pos, *widget.size, radius),
                width=border_w)

    def upd(*_):
        refs['bg'].pos  = widget.pos
        refs['bg'].size = widget.size
        if 'bd' in refs:
            refs['bd'].rounded_rectangle = (*widget.pos, *widget.size, radius)
    widget.bind(pos=upd, size=upd)
    return refs.get('bg')


# ══════════════════════════════════════════════════════════════════════════════
#  ThemedBackground — widget base que responde al ThemeManager
#  Úsalo como mixin o úsalo directamente como fondo de pantalla completa.
# ══════════════════════════════════════════════════════════════════════════════
class ThemedBackground(FloatLayout):
    """
    Widget de fondo que escucha al ThemeManager.
    Dibuja: color sólido + (opcional) imagen semitransparente encima.
    Regístrate con theme.register_widget(self) para actualizaciones.
    """
    def __init__(self, **kw):
        super().__init__(**kw)
        self._img_rect  = None
        self._img_color = None
        self._bg_color  = None
        self._bg_rect   = None
        self._build_canvas()
        theme.register_widget(self)

    def _build_canvas(self):
        self.canvas.before.clear()
        with self.canvas.before:
            # 1. Color sólido de fondo
            self._bg_color = Color(*theme.bg)
            self._bg_rect  = Rectangle(pos=self.pos, size=self.size)
            # 2. Imagen de fondo (si hay)
            if theme.bg_image and os.path.isfile(theme.bg_image):
                self._img_color = Color(1, 1, 1, theme.bg_opacity)
                self._img_rect  = Rectangle(
                    source=theme.bg_image,
                    pos=self.pos, size=self.size)
            else:
                self._img_color = None
                self._img_rect  = None
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        if self._bg_rect:
            self._bg_rect.pos  = self.pos
            self._bg_rect.size = self.size
        if self._img_rect:
            self._img_rect.pos  = self.pos
            self._img_rect.size = self.size

    def on_theme_update(self):
        """Llamado por ThemeManager cuando cambia color o imagen."""
        self._build_canvas()


# ── GothicScrollView ──────────────────────────────────────────────────────────
class GothicScrollView(ScrollView):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bar_width          = dp(3)
        self.bar_color          = list(C_ACCENT)
        self.bar_inactive_color = list(C_BORDER)
        self.scroll_type        = ['bars', 'content']
        self.effect_cls         = 'ScrollEffect'

    def on_theme_update(self):
        self.bar_color          = list(theme.accent)
        self.bar_inactive_color = list(theme.border)


# ── SeekBar interactiva ───────────────────────────────────────────────────────
class SeekBar(Widget):
    progress = NumericProperty(0.0)
    on_seek  = ObjectProperty(None, allownone=True)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint_y = None
        self.height      = dp(16)
        self._dragging   = False
        self.bind(pos=self._rd, size=self._rd, progress=self._rd)
        theme.register_widget(self)

    def _rd(self, *_):
        if self.canvas is None:
            return
        self.canvas.clear()
        w, h = self.size
        x, y = self.pos
        if w <= 0:
            return
        bh = h * 0.38
        by = y + (h - bh) / 2
        with self.canvas:
            Color(*theme.get('seekbar_bg'))
            RoundedRectangle(pos=(x, by), size=(w, bh), radius=[bh/2])
            fw = w * self.progress
            if fw > 0:
                Color(*theme.accent)
                RoundedRectangle(pos=(x, by), size=(fw, bh), radius=[bh/2])
            tx = x + fw
            tr = dp(7)
            Color(*theme.gold)
            Ellipse(pos=(tx - tr, y + h/2 - tr), size=(tr*2, tr*2))
            Color(*theme.gold_dark)
            Line(circle=(tx, y + h/2, tr - dp(1)), width=1.2)

    def on_theme_update(self):
        self._rd()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._dragging = True
            self._upd_seek(touch.x)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._dragging:
            self._upd_seek(touch.x)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._dragging:
            self._dragging = False
            self._upd_seek(touch.x)
            return True
        return super().on_touch_up(touch)

    def _upd_seek(self, tx):
        if self.width > 0:
            val = max(0.0, min(1.0, (tx - self.x) / self.width))
            self.progress = val
            if self.on_seek:
                self.on_seek(val)
