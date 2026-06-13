"""
Header de página — Gothic Player
Usa el asset gothic_frames.png para el marco ornamental superior.
"""
import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label     import Label
from kivy.graphics      import Color, Rectangle, Line, Ellipse
from kivy.metrics       import dp, sp
from ui.theme           import theme


class PageHeader(BoxLayout):
    def __init__(self, title='', right_widgets=None, **kw):
        super().__init__(**kw)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height      = dp(62)
        self.padding     = [dp(20), dp(12), dp(20), dp(8)]
        self.spacing     = dp(10)

        with self.canvas.before:
            # Fondo semitransparente
            self._c_bg   = Color(*theme.bg2[:3], 0.45)
            self._bg     = Rectangle(pos=self.pos, size=self.size)

            # Línea dorada inferior
            self._c_line = Color(*theme.gold_dark)
            self._line   = Line(
                points=[self.x, self.y, self.right, self.y], width=1.5)
            # Diamante central
            self._c_dot  = Color(*theme.gold)
            self._dot    = Ellipse(
                pos=(self.center_x - dp(3), self.y - dp(3)),
                size=(dp(6), dp(6)))
        self.bind(pos=self._upd, size=self._upd)

        self._deco = Label(
            text='//', color=list(theme.gold_muted), font_size=sp(16),
            size_hint=(None, 1), width=dp(30), halign='center', bold=True)
        self.add_widget(self._deco)

        self._title_lbl = Label(
            text=title.upper(), color=list(theme.gold),
            font_size=sp(22), bold=True, halign='left')
        self._title_lbl.bind(
            size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        self.add_widget(self._title_lbl)
        self.add_widget(BoxLayout())

        if right_widgets:
            for w in right_widgets:
                self.add_widget(w)

        theme.register_widget(self)

    def _upd(self, *_):
        self._bg.pos    = self.pos
        self._bg.size   = self.size
        self._line.points = [self.x, self.y, self.right, self.y]
        self._dot.pos   = (self.center_x - dp(3), self.y - dp(3))

    def on_theme_update(self):
        self._c_bg.rgba   = (*theme.bg2[:3], 0.45)
        self._c_line.rgba = list(theme.gold_dark)
        self._c_dot.rgba  = list(theme.gold)
        self._deco.color  = list(theme.gold_muted)
        self._title_lbl.color = list(theme.gold)
