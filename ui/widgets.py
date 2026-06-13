"""
Widgets reutilizables — Gothic Player
Todos los widgets con Color objects se registran en ThemeManager
para recibir on_theme_update() y actualizarse en tiempo real.
"""
from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button     import Button
from kivy.uix.label      import Label
from kivy.uix.textinput  import TextInput
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.metrics  import dp, sp
from kivy.properties import (BooleanProperty, NumericProperty,
                              StringProperty, ListProperty)
from kivy.clock import Clock
from config    import hex_to_rgba, GOTHIC_THEME as T
from ui.theme  import (C_BG, C_BG2, C_SURFACE, C_SURFACE_L, C_SURFACE_H,
                       C_ACCENT, C_ACCENT_H, C_GOLD, C_GOLD_D, C_GOLD_M,
                       C_TEXT, C_TEXT_SEC, C_TEXT_MUT, C_BORDER, C_BORDER_G,
                       C_TRANS, C_SEEK_BG, C_SEEK_FILL, C_SEEK_THUMB, theme)


# ── PrimaryBtn ────────────────────────────────────────────────────────────────
class PrimaryBtn(Button):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.color             = list(theme.text)
        self.font_size         = sp(13)
        self.bold              = True
        self.size_hint_y       = None
        self.height            = dp(44)
        with self.canvas.before:
            self._c_fill = Color(*theme.accent)
            self._r_fill = RoundedRectangle(pos=self.pos, size=self.size,
                                            radius=[dp(8)])
        self.bind(pos=self._upd, size=self._upd, state=self._on_st)
        theme.register_widget(self)

    def _upd(self, *_):
        self._r_fill.pos  = self.pos
        self._r_fill.size = self.size

    def _on_st(self, *_):
        self._c_fill.rgba = list(theme.accent_hover if self.state == 'down'
                                 else theme.accent)

    def on_theme_update(self):
        self._c_fill.rgba = list(theme.accent)
        self.color = list(theme.text)


# ── SecondaryBtn ──────────────────────────────────────────────────────────────
class SecondaryBtn(Button):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.color             = list(theme.gold)
        self.font_size         = sp(12)
        self.bold              = True
        self.size_hint_y       = None
        self.height            = dp(36)
        with self.canvas.before:
            self._c_fill = Color(*theme.surface_light)
            self._r_fill = RoundedRectangle(pos=self.pos, size=self.size,
                                            radius=[dp(8)])
            self._c_brd  = Color(*theme.gold_dark)
            self._r_brd  = Line(
                rounded_rectangle=(*self.pos, *self.size, dp(8)), width=1.2)
        self.bind(pos=self._upd, size=self._upd, state=self._on_st)
        theme.register_widget(self)

    def _upd(self, *_):
        self._r_fill.pos  = self.pos
        self._r_fill.size = self.size
        self._r_brd.rounded_rectangle = (*self.pos, *self.size, dp(8))

    def _on_st(self, *_):
        self._c_fill.rgba = list(theme.get('surface_hover')
                                 if self.state == 'down'
                                 else theme.surface_light)

    def on_theme_update(self):
        self._c_fill.rgba = list(theme.surface_light)
        self._c_brd.rgba  = list(theme.gold_dark)
        self.color = list(theme.gold)


# ── GothicInput ───────────────────────────────────────────────────────────────
class GothicInput(TextInput):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_color  = (0, 0, 0, 0)
        self.background_normal = ''
        self.background_active = ''
        self.foreground_color  = list(theme.text)
        self.hint_text_color   = list(theme.text_muted)
        self.cursor_color      = list(theme.gold)
        self.selection_color   = [*list(theme.accent[:3]), 0.45]
        self.font_size         = sp(13)
        self.padding           = [dp(14), dp(10), dp(14), dp(10)]
        self.size_hint_y       = None
        self.height            = dp(48)
        self.multiline         = False
        with self.canvas.before:
            self._c_bg  = Color(*theme.surface)
            self._r_bg  = RoundedRectangle(pos=self.pos, size=self.size,
                                           radius=[dp(10)])
            self._c_brd = Color(*theme.gold_dark)
            self._r_brd = Line(
                rounded_rectangle=(*self.pos, *self.size, dp(10)), width=1.2)
        self.bind(pos=self._upd, size=self._upd, focus=self._on_focus)
        theme.register_widget(self)

    def _upd(self, *_):
        self._r_bg.pos  = self.pos
        self._r_bg.size = self.size
        self._r_brd.rounded_rectangle = (*self.pos, *self.size, dp(10))

    def _on_focus(self, *_):
        self._c_brd.rgba  = list(theme.gold if self.focus else theme.gold_dark)
        self._r_brd.width = 1.8 if self.focus else 1.2

    def on_theme_update(self):
        self._c_bg.rgba  = (*theme.surface[:3], 0.72)
        self._c_brd.rgba = list(theme.gold_dark)
        self.foreground_color = list(theme.text)
        self.hint_text_color  = list(theme.text_muted)
        self.cursor_color     = list(theme.gold)


# ── GothicCard ────────────────────────────────────────────────────────────────
class GothicCard(BoxLayout):
    def __init__(self, bg=None, border=None, radius=dp(12), **kw):
        super().__init__(**kw)
        r = radius
        with self.canvas.before:
            self._c_bg = Color(*(bg or (*theme.surface[:3], 0.75)))
            self._r_bg = RoundedRectangle(pos=self.pos, size=self.size,
                                          radius=[r])
            self._c_bd = Color(*(border or theme.gold_dark))
            self._r_bd = Line(
                rounded_rectangle=(*self.pos, *self.size, r), width=1.2)
        self.bind(pos=self._upd, size=self._upd)
        theme.register_widget(self)

    def _upd(self, *_):
        self._r_bg.pos  = self.pos
        self._r_bg.size = self.size
        self._r_bd.rounded_rectangle = (*self.pos, *self.size,
                                        self._r_bg.radius[0])

    def on_theme_update(self):
        self._c_bg.rgba = (*theme.surface[:3], 0.75)
        self._c_bd.rgba = list(theme.gold_dark)


# ── GothicSep ─────────────────────────────────────────────────────────────────
class GothicSep(BoxLayout):
    def __init__(self, color=None, **kw):
        super().__init__(**kw)
        self.size_hint_y = None
        self.height      = dp(1)
        with self.canvas:
            self._c = Color(*(color or theme.gold_dark))
            self._r = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._r, 'pos', self.pos),
                  size=lambda *_: setattr(self._r, 'size', self.size))
        theme.register_widget(self)

    def on_theme_update(self):
        self._c.rgba = list(theme.gold_dark)


# ── GothicToggle ──────────────────────────────────────────────────────────────
class GothicToggle(BoxLayout):
    active = BooleanProperty(False)
    label  = StringProperty('')

    def __init__(self, **kw):
        super().__init__(**kw)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height      = dp(50)
        self.spacing     = dp(12)
        self.padding     = [dp(16), dp(8)]
        with self.canvas.before:
            self._c_bg = Color(*theme.surface[:3], 0.72)
            self._r_bg = RoundedRectangle(pos=self.pos, size=self.size,
                                          radius=[dp(10)])
        self.bind(pos=self._upd_bg, size=self._upd_bg)
        self._lbl = Label(text=self.label, color=list(theme.text),
                          font_size=sp(13), halign='left', bold=True)
        self._lbl.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        self.add_widget(self._lbl)
        self.bind(label=lambda *_: setattr(self._lbl, 'text', self.label))
        self._knob_w = FloatLayout(size_hint=(None, None), size=(dp(52), dp(28)))
        self.add_widget(self._knob_w)
        Clock.schedule_once(self._draw_knob, 0)
        self.bind(active=self._draw_knob)
        theme.register_widget(self)

    def _upd_bg(self, *_):
        self._r_bg.pos  = self.pos
        self._r_bg.size = self.size

    def _draw_knob(self, *_):
        kw = self._knob_w
        with kw.canvas:
            Color(*(theme.gold if self.active else theme.text_muted))
            RoundedRectangle(pos=kw.pos, size=kw.size, radius=[dp(14)])
            Color(1, 1, 1, 1)
            ox = dp(26) if self.active else dp(2)
            Ellipse(pos=(kw.x + ox, kw.y + dp(2)), size=(dp(24), dp(24)))
        kw.bind(pos=self._draw_knob, size=self._draw_knob)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.active = not self.active
            return True
        return super().on_touch_down(touch)

    def on_theme_update(self):
        self._c_bg.rgba = (*theme.surface[:3], 0.75)
        self._lbl.color = list(theme.text)
        self._draw_knob()


# ── GothicProgress ────────────────────────────────────────────────────────────
class GothicProgress(BoxLayout):
    value = NumericProperty(0)
    max   = NumericProperty(100)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint_y = None
        self.height      = dp(8)
        with self.canvas:
            self._c_bg   = Color(*theme.get('seekbar_bg')[:3], 0.70)
            self._r_bg   = RoundedRectangle(pos=self.pos, size=self.size,
                                            radius=[dp(4)])
            self._c_fill = Color(*theme.accent)
            self._r_fill = RoundedRectangle(pos=self.pos, size=(0, self.height),
                                            radius=[dp(4)])
        self.bind(pos=self._upd, size=self._upd, value=self._upd)
        theme.register_widget(self)

    def _upd(self, *_):
        self._r_bg.pos  = self.pos
        self._r_bg.size = self.size
        ratio = self.value / self.max if self.max > 0 else 0
        self._r_fill.pos  = self.pos
        self._r_fill.size = (self.width * ratio, self.height)

    def on_theme_update(self):
        self._c_bg.rgba   = (* theme.get('seekbar_bg')[:3], 0.70)
        self._c_fill.rgba = list(theme.accent)


# ── SettingRow ────────────────────────────────────────────────────────────────
class SettingRow(BoxLayout):
    def __init__(self, title='', subtitle='', **kw):
        super().__init__(**kw)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height      = dp(56)
        self.spacing     = dp(10)
        self.padding     = [dp(16), dp(4)]
        left = BoxLayout(orientation='vertical')
        self._t = Label(text=title, color=list(theme.text),
                        font_size=sp(13), bold=True, halign='left')
        self._t.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        left.add_widget(self._t)
        if subtitle:
            self._s = Label(text=subtitle, color=list(theme.text_muted),
                            font_size=sp(11), halign='left', italic=True)
            self._s.bind(size=lambda w, s2: setattr(w, 'text_size', (s2[0], None)))
            left.add_widget(self._s)
        else:
            self._s = None
        self.add_widget(left)
        theme.register_widget(self)

    def on_theme_update(self):
        self._t.color = list(theme.text)
        if self._s:
            self._s.color = list(theme.text_muted)


# ── NavItem ───────────────────────────────────────────────────────────────────
class NavItem(Button):
    active = BooleanProperty(False)

    def __init__(self, icon='', label='', **kw):
        active_val = kw.pop('active', False)
        super().__init__(**kw)
        self.text              = f'  {label}'
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.font_size         = sp(13)
        self.halign            = 'left'
        self.size_hint_y       = None
        self.height            = dp(48)
        with self.canvas.before:
            self._c_bg  = Color(0, 0, 0, 0)
            self._r_bg  = RoundedRectangle(pos=self.pos, size=self.size,
                                           radius=[dp(8)])
            self._c_brd = Color(0, 0, 0, 0)
            self._r_brd = Line(
                rounded_rectangle=(*self.pos, *self.size, dp(8)), width=1.2)
        self.bind(pos=self._upd_geo, size=self._upd_geo, state=self._refresh)
        self.active = active_val
        theme.register_widget(self)

    def _upd_geo(self, *_):
        self._r_bg.pos  = self.pos
        self._r_bg.size = self.size
        self._r_brd.rounded_rectangle = (*self.pos, *self.size, dp(8))

    def on_active(self, instance, value):
        self._refresh()

    def _refresh(self, *_):
        if self.active:
            self._c_bg.rgba  = (*theme.accent[:3], 0.92)
            self._c_brd.rgba = list(theme.accent_hover)
            self.color       = list(theme.gold)
        elif self.state == 'down':
            self._c_bg.rgba  = (*theme.get('surface_hover')[:3], 0.82)
            self._c_brd.rgba = (0, 0, 0, 0)
            self.color       = list(theme.text)
        else:
            self._c_bg.rgba  = (0, 0, 0, 0)
            self._c_brd.rgba = (0, 0, 0, 0)
            self.color       = list(theme.text_sec)

    def on_theme_update(self):
        self._refresh()
