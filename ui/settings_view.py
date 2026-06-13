"""
Settings — Gothic Player Pro
Colores y fondo de imagen se aplican en tiempo real via ThemeManager.
"""
import os
from pathlib import Path
from kivy.uix.boxlayout   import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview  import ScrollView
from kivy.uix.label       import Label
from kivy.uix.button      import Button
from kivy.uix.slider      import Slider
from kivy.uix.popup       import Popup
from kivy.uix.image       import AsyncImage
from kivy.graphics        import (Color, Rectangle, RoundedRectangle,
                                   Line, Ellipse)
from kivy.metrics         import dp, sp
from kivy.clock           import Clock
from kivy.properties      import BooleanProperty, StringProperty

from ui.theme  import (C_BG, C_BG2, C_SURFACE, C_SURFACE_L, C_SURFACE_H,
                        C_ACCENT, C_ACCENT_H, C_GOLD, C_GOLD_D, C_GOLD_M,
                        C_TEXT, C_TEXT_SEC, C_TEXT_MUT,
                        C_SEEK_BG, C_SEEK_FILL, C_SEEK_THUMB,
                        GothicScrollView, draw_bg, theme)
from ui.widgets import PrimaryBtn, SecondaryBtn, GothicInput
from ui.header  import PageHeader
from config     import app_config, hex_to_rgba, GOTHIC_THEME as T


# ── Toggle switch ─────────────────────────────────────────────────────────────
class _SwitchKnob(FloatLayout):
    def __init__(self, active=False, **kw):
        super().__init__(**kw)
        self.size_hint  = (None, None)
        self.size       = (dp(54), dp(28))
        self._active    = active
        self.register_event_type('on_toggle')
        with self.canvas:
            self._c_track = Color(*(list(theme.gold) if active
                                    else list(theme.text_muted)))
            self._r_track = RoundedRectangle(pos=self.pos, size=self.size,
                                             radius=[dp(14)])
            Color(1, 1, 1, 1)
            kx = (self.x + self.width - dp(26)
                  if active else self.x + dp(2))
            self._r_knob = Ellipse(pos=(kx, self.y + dp(2)),
                                   size=(dp(24), dp(24)))
        self.bind(pos=self._rd, size=self._rd, on_touch_down=self._tap)

    def _rd(self, *_):
        self._r_track.pos    = self.pos
        self._r_track.size   = self.size
        self._r_track.radius = [dp(14)]
        kx = (self.x + self.width - dp(26)
              if self._active else self.x + dp(2))
        self._r_knob.pos = (kx, self.y + dp(2))

    def set_active(self, val, animate=True):
        self._active = val
        self._c_track.rgba = list(theme.gold) if val else list(theme.text_muted)
        self._rd()

    def _tap(self, _, touch):
        if self.collide_point(*touch.pos):
            self._active = not self._active
            self._c_track.rgba = (list(theme.gold)
                                  if self._active else list(theme.text_muted))
            self._rd()
            self.dispatch('on_toggle', self._active)
            return True
        return False

    def on_toggle(self, *_): pass


class _Toggle(BoxLayout):
    active = BooleanProperty(False)

    def __init__(self, label='', sublabel='', initial=False,
                 on_change=None, **kw):
        super().__init__(**kw)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height      = dp(52)
        self.padding     = [dp(16), dp(6)]
        self.spacing     = dp(12)
        self._cb         = on_change
        with self.canvas.before:
            self._c_row = Color(*theme.surface[:3], 0.58)
            self._row = RoundedRectangle(pos=self.pos, size=self.size,
                                         radius=[dp(8)])
        theme.register_widget(self)
        self.bind(pos=self._upd, size=self._upd)

        txt = BoxLayout(orientation='vertical')
        lm  = Label(text=label, color=list(theme.text), font_size=sp(13),
                    bold=True, halign='left')
        lm.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        txt.add_widget(lm)
        if sublabel:
            ls = Label(text=sublabel, color=list(theme.text_muted), font_size=sp(10),
                       halign='left', italic=True)
            ls.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
            txt.add_widget(ls)
        self.add_widget(txt)
        self.add_widget(BoxLayout())

        self._sw = _SwitchKnob(active=initial)
        self._sw.bind(on_toggle=self._toggled)
        self.add_widget(self._sw)
        self.active = initial
        self.bind(active=self._on_active)

    def on_theme_update(self):
        self._c_row.rgba = (*theme.surface[:3], 0.58)

    def _upd(self, *_):
        self._row.pos  = self.pos
        self._row.size = self.size

    def _toggled(self, sw, val):
        self.active = val
        if self._cb:
            self._cb(val)

    def _on_active(self, _, val):
        self._sw.set_active(val, animate=False)


# ── Slider con estilo gótico ──────────────────────────────────────────────────
class _SettSlider(Slider):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.cursor_image = ''
        self.cursor_size  = (1, 1)
        self.bind(pos=self._rd, size=self._rd, value=self._rd)

    def _rd(self, *_):
        self.canvas.after.clear()
        with self.canvas.after:
            y  = self.center_y
            x0 = self.x + dp(8)
            tw = self.width - dp(16)
            h  = dp(6)
            Color(*theme.get("seekbar_bg"))
            RoundedRectangle(pos=(x0, y-h/2), size=(tw, h), radius=[h/2])
            r = ((self.value - self.min) / (self.max - self.min)
                 if self.max > self.min else 0)
            if r > 0:
                Color(*theme.accent)
                RoundedRectangle(pos=(x0, y-h/2), size=(tw*r, h), radius=[h/2])
            tx = x0 + tw * r
            tr = dp(12)
            Color(*theme.gold)
            Ellipse(pos=(tx-tr, y-tr), size=(tr*2, tr*2))
            Color(*theme.gold_dark)
            Line(circle=(tx, y, tr-1), width=1.2)


# ── Chip de formato ───────────────────────────────────────────────────────────
class _FmtChip(Button):
    def __init__(self, label, active=False, **kw):
        super().__init__(text=label, **kw)
        self._active           = active
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.font_size         = sp(12)
        self.bold              = True
        self.size_hint         = (None, None)
        self.size              = (dp(62), dp(36))
        with self.canvas.before:
            self._c = Color(*(list(theme.accent) if active else list(theme.surface_light)))
            self._r = RoundedRectangle(pos=self.pos, size=self.size,
                                       radius=[dp(18)])
            Color(*theme.gold_dark)
            self._l = Line(rounded_rectangle=(*self.pos, *self.size, dp(18)),
                           width=1.0)
        self.color = list(theme.text if active else theme.text_sec)
        self.bind(pos=self._upd, size=self._upd)

    def set_active(self, v):
        self._active = v
        self._c.rgba = list(theme.accent if v else C_SURFACE_L)
        self.color   = list(theme.text if v else theme.text_sec)

    def _upd(self, *_):
        self._r.pos  = self.pos
        self._r.size = self.size
        self._l.rounded_rectangle = (*self.pos, *self.size, dp(18))


# ── Punto de color ────────────────────────────────────────────────────────────
class _ColorDot(Button):
    def __init__(self, color, active=False, on_select=None, **kw):
        super().__init__(**kw)
        self._color_hex        = color
        self._active           = active
        self._on_sel           = on_select
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.size_hint         = (None, None)
        self.size              = (dp(40), dp(40))
        self.text              = ''
        with self.canvas:
            Color(*hex_to_rgba(color))
            self._e  = Ellipse(pos=(self.x+dp(3), self.y+dp(3)),
                               size=(self.width-dp(6), self.height-dp(6)))
            self._cr = Color(1, 1, 1, 0.95 if active else 0)
            self._rl = Line(
                circle=(self.center_x, self.center_y, self.width/2-dp(4)),
                width=2.4)
        self.bind(pos=self._upd, size=self._upd, on_release=self._sel)
        theme.register_widget(self)

    def _upd(self, *_):
        self._e.pos  = (self.x+dp(3), self.y+dp(3))
        self._e.size = (self.width-dp(6), self.height-dp(6))
        self._rl.circle = (self.center_x, self.center_y, self.width/2-dp(4))

    def set_active(self, v):
        self._active = v
        self._cr.a   = 0.95 if v else 0

    def _sel(self, *_):
        self.set_active(True)
        if self._on_sel:
            self._on_sel(self._color_hex)


# ── Miniatura de imagen de fondo ──────────────────────────────────────────────
class _BgThumb(Button):
    """Miniatura clicable que representa una opción de fondo."""
    def __init__(self, source='', label='', active=False, on_select=None, **kw):
        super().__init__(**kw)
        self._source    = source   # ruta de archivo o '' para color sólido
        self._active    = active
        self._on_sel    = on_select
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.size_hint  = (None, None)
        self.size       = (dp(72), dp(52))
        self.text       = ''

        with self.canvas.before:
            # Marco redondeado
            self._c_border = Color(*(list(theme.gold) if active else list(theme.surface_light)))
            self._r_border = RoundedRectangle(pos=self.pos, size=self.size,
                                              radius=[dp(8)])
            # Interior — color de fondo real
            self._c_inner = Color(*theme.bg[:3], 0.85)
            self._r_inner  = RoundedRectangle(
                pos=(self.x+dp(2), self.y+dp(2)),
                size=(self.width-dp(4), self.height-dp(4)),
                radius=[dp(6)])
            if source and os.path.isfile(source):
                # Imagen con transparencia para preview real del efecto
                self._c_img = Color(1, 1, 1, theme.bg_opacity)
                self._r_img = Rectangle(
                    source=source,
                    pos=(self.x+dp(2), self.y+dp(2)),
                    size=(self.width-dp(4), self.height-dp(4)))
            else:
                self._c_img = None
                self._r_img = None

        # Etiqueta debajo
        if label:
            lbl = Label(
                text=label, color=list(theme.text_muted), font_size=sp(9),
                halign='center', size_hint=(1, None), height=dp(14),
                pos_hint={'center_x': .5})
            # No podemos añadir label fácilmente sin FloatLayout, se omite aquí

        self.bind(pos=self._upd, size=self._upd, on_release=self._sel)
        theme.register_widget(self)

    def _upd(self, *_):
        self._r_border.pos  = self.pos
        self._r_border.size = self.size
        self._r_inner.pos   = (self.x+dp(2), self.y+dp(2))
        self._r_inner.size  = (self.width-dp(4), self.height-dp(4))
        if self._r_img:
            self._r_img.pos  = (self.x+dp(2), self.y+dp(2))
            self._r_img.size = (self.width-dp(4), self.height-dp(4))

    def on_theme_update(self):
        self._c_inner.rgba  = (*theme.bg[:3], 0.85)
        self._c_border.rgba = list(theme.gold if self._active else theme.surface_light)
        if self._c_img:
            self._c_img.rgba = (1, 1, 1, theme.bg_opacity)

    def set_active(self, v):
        self._active = v
        self._c_border.rgba = list(theme.gold) if v else list(theme.surface_light)

    def _sel(self, *_):
        self.set_active(True)
        if self._on_sel:
            self._on_sel(self._source)


# ── Card de sección ───────────────────────────────────────────────────────────
class _SCard(BoxLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.spacing     = dp(2)
        self.padding     = [dp(14), dp(10)]
        self.bind(minimum_height=self.setter('height'))
        with self.canvas.before:
            self._c_bg = Color(*theme.surface[:3], 0.68)
            self._r = RoundedRectangle(pos=self.pos, size=self.size,
                                       radius=[dp(12)])
            self._c_bd = Color(*theme.gold_dark)
            self._l = Line(rounded_rectangle=(*self.pos, *self.size, dp(12)),
                           width=1.0)
        self.bind(pos=self._upd, size=self._upd)
        theme.register_widget(self)

    def _upd(self, *_):
        self._r.pos  = self.pos
        self._r.size = self.size
        self._l.rounded_rectangle = (*self.pos, *self.size, dp(12))

    def on_theme_update(self):
        self._c_bg.rgba = (*theme.surface[:3], 0.68)
        self._c_bd.rgba = list(theme.gold_dark)


def _Lbl(text):
    l = Label(text=text, color=list(theme.text), font_size=sp(13),
              halign='left', size_hint_y=None, height=dp(28), bold=True)
    l.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
    return l


def _SubLbl(text):
    l = Label(text=text, color=list(theme.text_muted), font_size=sp(11),
              halign='left', size_hint_y=None, height=dp(20), italic=True)
    l.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
    return l


def _Div():
    d = BoxLayout(size_hint_y=None, height=dp(1))
    with d.canvas:
        Color(*theme.gold_dark)
        _r = Rectangle(pos=d.pos, size=d.size)
    d.bind(pos=lambda *_: setattr(_r, 'pos', d.pos),
           size=lambda *_: setattr(_r, 'size', d.size))
    return d


def _SecHdr(text):
    box = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8),
                    padding=[dp(4), 0])
    box.add_widget(Label(text='>', color=list(theme.gold_muted), font_size=sp(14),
                         size_hint=(None, 1), width=dp(18), halign='center'))
    box.add_widget(Label(text=text, color=list(theme.gold), font_size=sp(13),
                         bold=True, halign='left'))
    return box


# ══════════════════════════════════════════════════════════════════════════════
#  SettingsView
# ══════════════════════════════════════════════════════════════════════════════
class SettingsView(BoxLayout):
    def __init__(self, on_vol_change=None, on_theme_change=None, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'
        self._on_vol     = on_vol_change
        self._on_theme   = on_theme_change
        with self.canvas.before:
            self._c_bg = Color(*theme.bg[:3], 0.0)
            self._r_bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd_bg, size=self._upd_bg)
        theme.register_widget(self)
        self.add_widget(PageHeader(title='Settings'))

        sv = GothicScrollView()
        self._inner = BoxLayout(
            orientation='vertical', size_hint_y=None,
            spacing=dp(12), padding=[dp(20), dp(14), dp(20), dp(30)],
        )
        self._inner.bind(minimum_height=self._inner.setter('height'))
        sv.add_widget(self._inner)
        self.add_widget(sv)
        self._build()

    def _upd_bg(self, *_):
        self._r_bg.pos  = self.pos
        self._r_bg.size = self.size

    def on_theme_update(self):
        self._c_bg.rgba = (*theme.bg[:3], 0.0)

    def _build(self):
        self._build_playback()
        self._build_downloads()
        self._build_appearance()
        self._build_about()
        self._inner.add_widget(self._build_save())

    # ── PLAYBACK ──────────────────────────────────────────────────────────────
    def _build_playback(self):
        self._inner.add_widget(_SecHdr('PLAYBACK'))
        card = _SCard()

        card.add_widget(_Lbl('Default Volume'))
        vr = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        self._vol_sl  = _SettSlider(min=0, max=100,
                                    value=app_config.get('volume', 70))
        self._lbl_vol = Label(
            text=f"{int(app_config.get('volume', 70))}%",
            color=list(theme.gold), font_size=sp(15), bold=True,
            size_hint=(None, 1), width=dp(54), halign='center')
        self._vol_sl.bind(value=self._vol_changed)
        vr.add_widget(self._vol_sl)
        vr.add_widget(self._lbl_vol)
        card.add_widget(vr)
        card.add_widget(_Div())

        self._tog_cont = _Toggle(
            label='Continuous playback',
            sublabel='Reproduce la siguiente cancion automaticamente',
            initial=app_config.get('continuous', True),
            on_change=lambda v: app_config.set('continuous', v))
        self._tog_rep = _Toggle(
            label='Repeat playlist',
            sublabel='Vuelve al inicio al terminar la lista',
            initial=app_config.get('repeat', False),
            on_change=lambda v: app_config.set('repeat', v))
        self._tog_shuf = _Toggle(
            label='Shuffle by default',
            sublabel='Orden aleatorio al iniciar reproduccion',
            initial=app_config.get('shuffle', False),
            on_change=lambda v: app_config.set('shuffle', v))
        for t in (self._tog_cont, self._tog_rep, self._tog_shuf):
            card.add_widget(t)
            card.add_widget(_Div())
        self._inner.add_widget(card)

    # ── DOWNLOADS ─────────────────────────────────────────────────────────────
    def _build_downloads(self):
        self._inner.add_widget(_SecHdr('DOWNLOADS'))
        card = _SCard()
        card.add_widget(_Lbl('Download folder'))
        fr = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        self._fldr_lbl = Label(
            text=str(app_config.get_downloads_folder())[:60],
            color=list(theme.text_sec), font_size=sp(11), italic=True,
            halign='left')
        self._fldr_lbl.bind(
            size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        ch = SecondaryBtn(text='Change folder')
        ch.size_hint = (None, None)
        ch.size      = (dp(150), dp(36))
        ch.bind(on_release=lambda *_: self._pick_folder())
        fr.add_widget(self._fldr_lbl)
        fr.add_widget(ch)
        card.add_widget(fr)
        card.add_widget(_Div())

        card.add_widget(_Lbl('Default format'))
        card.add_widget(_SubLbl('Formato por defecto al descargar'))
        fmt_row = BoxLayout(size_hint_y=None, height=dp(46),
                            spacing=dp(8), padding=[0, dp(4)])
        saved = app_config.get('default_format', 'MP3')
        self._fmt_btns = {}
        for f in ['MP3', 'FLAC', 'WAV', 'MP4', 'MKV']:
            b = _FmtChip(f, active=(f == saved))
            b.bind(on_release=lambda btn, fmt=f: self._set_fmt(fmt))
            self._fmt_btns[f] = b
            fmt_row.add_widget(b)
        fmt_row.add_widget(BoxLayout())
        card.add_widget(fmt_row)
        self._inner.add_widget(card)

    # ── APPEARANCE ────────────────────────────────────────────────────────────
    def _build_appearance(self):
        self._inner.add_widget(_SecHdr('APPEARANCE'))

        # ── Accent Color ──────────────────────────────────────────────────────
        card_acc = _SCard()
        card_acc.add_widget(_Lbl('Accent Color'))
        card_acc.add_widget(_SubLbl('Color principal de botones y seekbar'))
        acc_cols = ['#6B1B2D','#8B1538','#7B2D8B','#2D5A8B',
                    '#2D5A3D','#8B6914','#444444','#1A1A1A']
        saved_acc = app_config.get('accent_color', '#6B1B2D')
        self._acc_dots = []
        acc_row = BoxLayout(size_hint_y=None, height=dp(56),
                            spacing=dp(8), padding=[dp(2), dp(8)])
        for clr in acc_cols:
            d = _ColorDot(color=clr, active=(clr == saved_acc),
                          on_select=lambda c: self._apply_accent(c))
            self._acc_dots.append(d)
            acc_row.add_widget(d)
        acc_row.add_widget(BoxLayout())
        card_acc.add_widget(acc_row)
        self._inner.add_widget(card_acc)

        # ── Gold / Text Color ─────────────────────────────────────────────────
        card_gold = _SCard()
        card_gold.add_widget(_Lbl('Gold / Text Color'))
        card_gold.add_widget(_SubLbl('Color de titulos, ornamentos y seekbar thumb'))
        gold_cols = ['#C9A961','#E6C847','#DAA520','#FFD700',
                     '#CD853F','#B8860B','#FFFFFF','#AAAAAA']
        saved_gold = app_config.get('gold_color', '#C9A961')
        self._gold_dots = []
        gold_row = BoxLayout(size_hint_y=None, height=dp(56),
                             spacing=dp(8), padding=[dp(2), dp(8)])
        for clr in gold_cols:
            d = _ColorDot(color=clr, active=(clr == saved_gold),
                          on_select=lambda c: self._apply_gold(c))
            self._gold_dots.append(d)
            gold_row.add_widget(d)
        gold_row.add_widget(BoxLayout())
        card_gold.add_widget(gold_row)
        self._inner.add_widget(card_gold)

        # ── Background Color ──────────────────────────────────────────────────
        card_bg = _SCard()
        card_bg.add_widget(_Lbl('Background Color'))
        card_bg.add_widget(_SubLbl('Color de fondo principal (cuando no hay imagen)'))
        bg_cols = ['#0D0A0B','#0A0A0F','#080808','#060D06',
                   '#0D0A06','#0A0608','#111111','#1A1018']
        saved_bg = app_config.get('bg_color', '#0D0A0B')
        self._bg_dots = []
        bg_row = BoxLayout(size_hint_y=None, height=dp(56),
                           spacing=dp(8), padding=[dp(2), dp(8)])
        for clr in bg_cols:
            d = _ColorDot(color=clr, active=(clr == saved_bg),
                          on_select=lambda c: self._apply_bg(c))
            self._bg_dots.append(d)
            bg_row.add_widget(d)
        bg_row.add_widget(BoxLayout())
        card_bg.add_widget(bg_row)
        self._inner.add_widget(card_bg)

        # ── Surface Color ─────────────────────────────────────────────────────
        card_surf = _SCard()
        card_surf.add_widget(_Lbl('Card / Surface Color'))
        card_surf.add_widget(_SubLbl('Color de tarjetas y paneles internos'))
        surf_cols = ['#1E1820','#1A1A2E','#1A2E1A','#2E1A1A',
                     '#1E1E1E','#251520','#201825','#242018']
        saved_surf = app_config.get('surface_color', '#1E1820')
        self._surf_dots = []
        surf_row = BoxLayout(size_hint_y=None, height=dp(56),
                             spacing=dp(8), padding=[dp(2), dp(8)])
        for clr in surf_cols:
            d = _ColorDot(color=clr, active=(clr == saved_surf),
                          on_select=lambda c: self._apply_surface(c))
            self._surf_dots.append(d)
            surf_row.add_widget(d)
        surf_row.add_widget(BoxLayout())
        card_surf.add_widget(surf_row)
        self._inner.add_widget(card_surf)

        # ── Background Image ──────────────────────────────────────────────────
        self._build_bg_image()

        # ── Toggles de UI ─────────────────────────────────────────────────────
        card_ui = _SCard()
        self._tog_orn = _Toggle(
            label='Show gothic ornaments',
            sublabel='Muestra decoraciones goticas en la interfaz',
            initial=app_config.get('show_ornaments', True),
            on_change=lambda v: app_config.set('show_ornaments', v))
        self._tog_anim = _Toggle(
            label='Enable animations',
            sublabel='Transiciones y animaciones de la UI',
            initial=app_config.get('animations', True),
            on_change=lambda v: app_config.set('animations', v))
        card_ui.add_widget(self._tog_orn)
        card_ui.add_widget(_Div())
        card_ui.add_widget(self._tog_anim)
        self._inner.add_widget(card_ui)

    def _build_bg_image(self):
        """Sección de imagen de fondo con previsualizaciones y opacidad."""
        card = _SCard()
        card.add_widget(_Lbl('Background Image'))
        card.add_widget(_SubLbl('Imagen de fondo — se superpone al color con transparencia'))

        # Fila de opciones: Sin imagen + imágenes guardadas + botón agregar
        self._img_row = BoxLayout(size_hint_y=None, height=dp(66),
                                  spacing=dp(8), padding=[dp(2), dp(6)])

        # Opción: sin imagen (color sólido)
        saved_img = app_config.get('bg_image', '')
        none_thumb = _BgThumb(
            source='', label='Ninguna',
            active=(saved_img == ''),
            on_select=lambda s: self._apply_bg_image(s))
        none_thumb.size = (dp(64), dp(44))
        self._img_thumbs = [none_thumb]
        self._img_row.add_widget(none_thumb)

        # Imágenes ya guardadas por el usuario
        saved_imgs = app_config.get('bg_images_list', [])
        for img_path in saved_imgs:
            if os.path.isfile(img_path):
                self._add_img_thumb(img_path, saved_img == img_path)

        # Botón para agregar imagen nueva
        add_btn = Button(
            text='+ Imagen',
            background_normal='', background_down='',
            background_color=(0, 0, 0, 0),
            color=list(theme.gold), font_size=sp(11), bold=True,
            size_hint=(None, None), size=(dp(64), dp(44)))
        with add_btn.canvas.before:
            Color(*theme.surface_light)
            _ar = RoundedRectangle(pos=add_btn.pos, size=add_btn.size,
                                   radius=[dp(8)])
            Color(*theme.gold_dark)
            _al = Line(rounded_rectangle=(*add_btn.pos, *add_btn.size, dp(8)),
                       width=1.0, dash_offset=3, dash_length=4)
        add_btn.bind(
            pos=lambda w, p: (setattr(_ar, 'pos', p),
                              setattr(_al, 'rounded_rectangle',
                                      (*p, *w.size, dp(8)))),
            size=lambda w, s: (setattr(_ar, 'size', s),
                               setattr(_al, 'rounded_rectangle',
                                       (*w.pos, *s, dp(8)))),
            on_release=lambda *_: self._pick_bg_image())
        self._img_row.add_widget(add_btn)
        self._img_row.add_widget(BoxLayout())
        card.add_widget(self._img_row)
        card.add_widget(_Div())

        # Slider de opacidad de imagen
        card.add_widget(_Lbl('Image Opacity'))
        op_row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        saved_op = app_config.get('bg_opacity', 0.18)
        self._op_sl = _SettSlider(min=0.0, max=1.0, value=saved_op)
        self._lbl_op = Label(
            text=f'{int(saved_op*100)}%',
            color=list(theme.gold), font_size=sp(14), bold=True,
            size_hint=(None, 1), width=dp(50), halign='center')
        self._op_sl.bind(value=self._opacity_changed)
        op_row.add_widget(self._op_sl)
        op_row.add_widget(self._lbl_op)
        card.add_widget(op_row)
        self._inner.add_widget(card)

    def _add_img_thumb(self, path, active=False):
        """Agrega una miniatura de imagen a la fila."""
        thumb = _BgThumb(
            source=path, active=active,
            on_select=lambda s: self._apply_bg_image(s))
        thumb.size = (dp(64), dp(44))
        self._img_thumbs.append(thumb)
        # Insertar antes del botón "+" (último widget antes del spacer)
        # La fila tiene: none_thumb, [...imágenes...], add_btn, spacer
        children = list(self._img_row.children)
        # children está en orden inverso en Kivy
        # Insertar antes del penúltimo (spacer es el último = children[0])
        self._img_row.add_widget(thumb, index=1)  # antes del spacer

    # ── ABOUT ─────────────────────────────────────────────────────────────────
    def _build_about(self):
        self._inner.add_widget(_SecHdr('ABOUT'))
        card = _SCard()
        from kivy.utils import platform as kp
        for lbl, val in [('Application', 'Gothic Player Pro'),
                          ('Version', '3.0.0'),
                          ('Engine', 'Kivy 2.3'),
                          ('Platform', kp.capitalize())]:
            row = BoxLayout(size_hint_y=None, height=dp(40),
                            padding=[dp(4), dp(2)])
            row.add_widget(Label(text=lbl, color=list(theme.text_muted),
                                 font_size=sp(12), halign='left'))
            row.add_widget(Label(text=val, color=list(theme.text),
                                 font_size=sp(12), halign='right', bold=True))
            card.add_widget(row)
            card.add_widget(_Div())
        clr_btn = PrimaryBtn(text='Clear Covers Cache')
        clr_btn.bind(on_release=lambda *_: self._clear_cache())
        card.add_widget(clr_btn)
        self._inner.add_widget(card)

    def _build_save(self):
        btn = PrimaryBtn(text='SAVE SETTINGS')
        btn.height    = dp(54)
        btn.font_size = sp(14)
        btn.bind(on_release=lambda *_: self._save())
        return btn

    # ── Callbacks de volumen y formato ────────────────────────────────────────
    def _vol_changed(self, _, v):
        self._lbl_vol.text = f'{int(v)}%'
        app_config.set('volume', int(v))
        if self._on_vol:
            self._on_vol(v)

    def _set_fmt(self, fmt):
        app_config.set('default_format', fmt)
        for f, b in self._fmt_btns.items():
            b.set_active(f == fmt)

    # ── Callbacks de colores ──────────────────────────────────────────────────
    def _apply_accent(self, color):
        app_config.set('accent_color', color)
        for d in self._acc_dots:
            d.set_active(d._color_hex == color)
        theme.set_accent(color)
        self._toast_brief(f'Accent: {color}')

    def _apply_gold(self, color):
        app_config.set('gold_color', color)
        for d in self._gold_dots:
            d.set_active(d._color_hex == color)
        theme.set_gold(color)
        self._toast_brief(f'Gold: {color}')

    def _apply_bg(self, color):
        app_config.set('bg_color', color)
        for d in self._bg_dots:
            d.set_active(d._color_hex == color)
        theme.set_bg(color)
        self._toast_brief(f'Background: {color}')

    def _apply_surface(self, color):
        app_config.set('surface_color', color)
        for d in self._surf_dots:
            d.set_active(d._color_hex == color)
        theme.set_surface(color)
        self._toast_brief(f'Surface: {color}')

    # ── Callbacks de imagen de fondo ──────────────────────────────────────────
    def _apply_bg_image(self, path):
        """Aplica imagen de fondo (o la quita si path == '')."""
        app_config.set('bg_image', path)
        for t in self._img_thumbs:
            t.set_active(t._source == path)
        op = app_config.get('bg_opacity', 0.18)
        theme.set_bg_image(path, opacity=op)
        if path:
            self._toast_brief('Imagen de fondo aplicada')
        else:
            self._toast_brief('Fondo: color solido')

    def _opacity_changed(self, _, v):
        self._lbl_op.text = f'{int(v*100)}%'
        app_config.set('bg_opacity', round(v, 2))
        theme.set_bg_opacity(v)

    def _pick_bg_image(self):
        """Abre selector de archivo para elegir imagen de fondo."""
        from kivy.utils import platform
        if platform == 'android':
            self._bg_image_popup()
            return
        try:
            from tkinter import filedialog, Tk
            root = Tk()
            root.withdraw()
            path = filedialog.askopenfilename(
                title='Seleccionar imagen de fondo',
                filetypes=[
                    ('Imágenes', '*.png *.jpg *.jpeg *.webp *.bmp'),
                    ('Todos los archivos', '*.*'),
                ])
            root.destroy()
            if path and os.path.isfile(path):
                self._register_and_apply_image(path)
        except Exception:
            self._bg_image_popup()

    def _bg_image_popup(self):
        """Fallback popup para ingresar ruta de imagen a mano (Android/Linux)."""
        content = BoxLayout(orientation='vertical',
                            padding=dp(20), spacing=dp(12))
        content.add_widget(Label(
            text='Ruta de la imagen:', color=list(theme.gold),
            font_size=sp(13), size_hint_y=None, height=dp(24)))
        entry = GothicInput(
            hint_text='/sdcard/Pictures/mi_fondo.jpg',
            text=app_config.get('bg_image', ''))
        content.add_widget(entry)
        content.add_widget(Label(
            text='Formatos: PNG, JPG, WEBP, BMP',
            color=list(theme.text_muted), font_size=sp(10),
            size_hint_y=None, height=dp(18)))
        br = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(12))
        ok  = PrimaryBtn(text='Aplicar')
        can = SecondaryBtn(text='Cancelar')
        br.add_widget(ok)
        br.add_widget(can)
        content.add_widget(br)
        popup = Popup(
            title='Imagen de fondo', content=content,
            size_hint=(None, None), size=(dp(480), dp(240)),
            background_color=hex_to_rgba(T['surface']),
            title_color=list(theme.gold))

        def do_ok(*_):
            p = entry.text.strip()
            if p and os.path.isfile(p):
                self._register_and_apply_image(p)
            elif p:
                self._toast(f'Archivo no encontrado:\n{p}')
            popup.dismiss()
        ok.bind(on_release=do_ok)
        can.bind(on_release=popup.dismiss)
        popup.open()

    def _register_and_apply_image(self, path):
        """Guarda la ruta en la lista, agrega miniatura y aplica."""
        imgs = app_config.get('bg_images_list', [])
        if path not in imgs:
            imgs.append(path)
            app_config.set('bg_images_list', imgs)
            self._add_img_thumb(path, active=True)
        self._apply_bg_image(path)

    # ── Carpeta de descargas ──────────────────────────────────────────────────
    def _pick_folder(self):
        from kivy.utils import platform
        if platform == 'android':
            self._folder_popup()
            return
        try:
            from tkinter import filedialog, Tk
            root = Tk()
            root.withdraw()
            folder = filedialog.askdirectory(
                title='Select download folder',
                initialdir=str(app_config.get_downloads_folder()))
            root.destroy()
            if folder:
                self._apply_folder(folder)
        except Exception:
            self._folder_popup()

    def _folder_popup(self):
        content = BoxLayout(orientation='vertical',
                            padding=dp(20), spacing=dp(12))
        content.add_widget(Label(text='Folder path:', color=list(theme.gold),
                                 font_size=sp(13),
                                 size_hint_y=None, height=dp(24)))
        entry = GothicInput(text=str(app_config.get_downloads_folder()))
        content.add_widget(entry)
        br = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(12))
        ok  = PrimaryBtn(text='Apply')
        can = SecondaryBtn(text='Cancel')
        br.add_widget(ok)
        br.add_widget(can)
        content.add_widget(br)
        popup = Popup(
            title='Change folder', content=content,
            size_hint=(None, None), size=(dp(460), dp(220)),
            background_color=hex_to_rgba(T['surface']),
            title_color=list(theme.gold))
        def do_ok(*_):
            p = entry.text.strip()
            if p:
                self._apply_folder(p)
            popup.dismiss()
        ok.bind(on_release=do_ok)
        can.bind(on_release=popup.dismiss)
        popup.open()

    def _apply_folder(self, folder):
        app_config.set_downloads_folder(folder)
        self._fldr_lbl.text = folder[:60]
        try:
            from kivy.app import App
            root = App.get_running_app().root
            if hasattr(root, '_views') and 'downloads' in root._views:
                root._views['downloads']._set_folder(folder)
        except Exception:
            pass

    # ── Save / Cache ──────────────────────────────────────────────────────────
    def _save(self):
        app_config.save()
        self._toast('Settings saved!')

    def _clear_cache(self):
        from config import COVERS_FOLDER
        try:
            deleted = sum(1 for f in Path(COVERS_FOLDER).glob('*')
                          if f.is_file() and not f.unlink())
            self._toast(f'Cleared {deleted} cached covers')
        except Exception as e:
            self._toast(f'Error: {e}')

    # ── Toast helpers ─────────────────────────────────────────────────────────
    def _toast_brief(self, msg):
        """Toast mini — no bloquea la pantalla."""
        pass  # Se puede implementar un snackbar ligero si se desea

    def _toast(self, msg):
        popup = Popup(
            title='', separator_height=0,
            content=Label(text=msg, color=list(theme.gold),
                          font_size=sp(14), halign='center'),
            size_hint=(None, None), size=(dp(340), dp(88)),
            background_color=hex_to_rgba(T['surface']),
            title_color=list(theme.gold), auto_dismiss=True)
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.8)
