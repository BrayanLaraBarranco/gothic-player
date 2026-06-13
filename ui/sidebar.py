"""
Sidebar — Gothic Player Pro
Usa frame_sidebar.png del spritesheet de marcos góticos.
Calavera dibujada en canvas, ornamentos dorados.
"""
import os, math
from kivy.uix.boxlayout   import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label       import Label
from kivy.uix.button      import Button
from kivy.graphics        import (Color, Rectangle, RoundedRectangle,
                                   Line, Ellipse)
from kivy.metrics         import dp, sp
from kivy.properties      import ObjectProperty
from kivy.clock           import Clock
from ui.theme             import theme
from ui.widgets           import NavItem


class Sidebar(BoxLayout):
    on_navigate = ObjectProperty(None, allownone=True)

    NAV = [
        ('library',   'Library'),
        ('playlists', 'Playlists'),
        ('downloads', 'Downloads'),
        ('settings',  'Settings'),
    ]

    def __init__(self, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'
        self.size_hint   = (None, 1)
        self.width       = dp(170)
        self.padding     = [dp(10), dp(14), dp(8), dp(8)]
        self.spacing     = dp(2)
        self._active     = 'library'
        self._nav_btns   = {}
        self._ornament_labels = []

        with self.canvas.before:
            # Fondo semitransparente
            self._c_bg  = Color(*theme.bg2[:3], 0.75)
            self._bg    = Rectangle(pos=self.pos, size=self.size)

            # Borde dorado derecho doble
            self._c_d1 = Color(*theme.gold_dark)
            self._d1   = Line(points=[self.right-dp(1), self.y,
                                       self.right-dp(1), self.top], width=1.8)
            self._c_d2 = Color(*theme.gold_muted)
            self._d2   = Line(points=[self.right-dp(4), self.y+dp(10),
                                       self.right-dp(4), self.top-dp(10)],
                              width=0.7)
            self._corner = None

        self.bind(pos=self._upd, size=self._upd)
        self._build()
        theme.register_widget(self)

    def _upd(self, *_):
        self._bg.pos        = self.pos
        self._bg.size       = self.size
        self._d1.points = [self.right-dp(1), self.y, self.right-dp(1), self.top]
        self._d2.points = [self.right-dp(4), self.y+dp(10),
                           self.right-dp(4), self.top-dp(10)]

    def on_theme_update(self):
        self._c_bg.rgba  = (*theme.bg2[:3], 0.75)
        self._c_d1.rgba  = list(theme.gold_dark)
        self._c_d2.rgba  = list(theme.gold_muted)
        self._c_icon_bg.rgba = list(theme.accent)
        self._c_icon_bd.rgba = list(theme.gold)
        self._icon_lbl.color  = list(theme.gold)
        self._gothic_lbl.color = list(theme.gold)
        self._player_lbl.color = list(theme.gold_muted)
        for lbl in self._ornament_labels:
            lbl.color = list(theme.gold_muted)
        self._ver_lbl.color = list(theme.gold_muted)

    def _build(self):
        # ── Logo ──────────────────────────────────────────────────────────────
        logo_box = BoxLayout(orientation='vertical', size_hint_y=None,
                             height=dp(100), spacing=dp(2))

        icon_wrap = FloatLayout(size_hint_y=None, height=dp(58))
        self._icon_lbl = Label(
            text='M', color=list(theme.gold), font_size=sp(26), bold=True,
            size_hint=(None, None), size=(dp(50), dp(50)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5})
        with self._icon_lbl.canvas.before:
            self._c_icon_bg = Color(*theme.accent)
            _ibg = RoundedRectangle(pos=self._icon_lbl.pos,
                                    size=self._icon_lbl.size, radius=[dp(12)])
            self._c_icon_bd = Color(*theme.gold)
            _ibd = Line(rounded_rectangle=(*self._icon_lbl.pos,
                                           *self._icon_lbl.size, dp(12)), width=1.8)
        def _upd_icon(*_):
            _ibg.pos  = self._icon_lbl.pos
            _ibg.size = self._icon_lbl.size
            _ibd.rounded_rectangle = (*self._icon_lbl.pos,
                                      *self._icon_lbl.size, dp(12))
        self._icon_lbl.bind(pos=_upd_icon, size=_upd_icon)
        icon_wrap.add_widget(self._icon_lbl)
        logo_box.add_widget(icon_wrap)

        self._gothic_lbl = Label(
            text='GOTHIC', color=list(theme.gold),
            font_size=sp(16), bold=True, halign='center',
            size_hint_y=None, height=dp(22))
        self._player_lbl = Label(
            text='P L A Y E R', color=list(theme.gold_muted),
            font_size=sp(8), halign='center',
            size_hint_y=None, height=dp(12))
        logo_box.add_widget(self._gothic_lbl)
        logo_box.add_widget(self._player_lbl)
        self.add_widget(logo_box)

        self.add_widget(self._ornament_row())

        # ── Calavera ──────────────────────────────────────────────────────────

        # ── Navegación ────────────────────────────────────────────────────────
        for key, label in self.NAV:
            btn = NavItem(label=label, active=(key == 'library'))
            btn.font_size = sp(12)
            btn.height    = dp(40)
            btn.bind(on_release=lambda b, k=key: self._nav(k))
            self._nav_btns[key] = btn
            self.add_widget(btn)

        self.add_widget(BoxLayout())
        self.add_widget(self._ornament_row())

        self._ver_lbl = Label(
            text='Version 3.0.0', color=list(theme.gold_muted),
            font_size=sp(8), halign='center',
            size_hint_y=None, height=dp(16))
        self.add_widget(self._ver_lbl)

    def _ornament_row(self):
        box = BoxLayout(size_hint_y=None, height=dp(18), padding=[dp(4), dp(4)])
        lbl = Label(text='— ✦ —', color=list(theme.gold_muted),
                    font_size=sp(10), halign='center')
        self._ornament_labels.append(lbl)
        box.add_widget(lbl)
        return box

    def _nav(self, key):
        self._active = key
        for k, btn in self._nav_btns.items():
            btn.active = (k == key)
            btn._refresh()
        if self.on_navigate:
            self.on_navigate(key)

    def set_active(self, key):
        self._nav(key)
