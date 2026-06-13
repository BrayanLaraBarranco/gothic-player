"""
Vista de Playlists — grid de tarjetas con portada, nombre y conteo
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.metrics import dp, sp
from ui.theme import (theme, C_BG, C_SURFACE, C_SURFACE_L, C_SURFACE_H,
                      C_ACCENT, C_GOLD, C_GOLD_D, C_GOLD_M,
                      C_TEXT, C_TEXT_SEC, C_TEXT_MUT, GothicScrollView, draw_bg)
from ui.widgets import GothicInput, PrimaryBtn, GothicSep
from ui.header import PageHeader
from config import hex_to_rgba, GOTHIC_THEME as T


class PlaylistsView(BoxLayout):
    def __init__(self, pl_mgr, library, on_open=None, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'
        self._pl_mgr     = pl_mgr
        self._library    = library
        self._on_open    = on_open
        with self.canvas.before:
            self._c_bg = Color(*theme.bg[:3], 0.0)
            self._r_bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd_bg, size=self._upd_bg)
        theme.register_widget(self)

        # Header con boton "+ Create"
        create_btn = PrimaryBtn(
            text='+ Create',
            size_hint=(None, None),
            size=(dp(110), dp(38)),
        )
        create_btn.bind(on_release=lambda *_: self._create_dialog())
        self.add_widget(PageHeader(title='Playlists', right_widgets=[create_btn]))

        sv = GothicScrollView()
        self._grid = GridLayout(
            cols=3,
            size_hint_y=None,
            spacing=dp(16),
            padding=[dp(24), dp(16), dp(24), dp(24)],
        )
        self._grid.bind(minimum_height=self._grid.setter('height'))
        sv.add_widget(self._grid)
        self.add_widget(sv)
        self.refresh()

    def _upd_bg(self, *_):
        self._r_bg.pos  = self.pos
        self._r_bg.size = self.size

    def on_theme_update(self):
        self._c_bg.rgba = (*theme.bg[:3], 0.0)
        self.refresh()

    def refresh(self):
        self._grid.clear_widgets()
        for name in self._pl_mgr.get_all_playlists():
            songs = self._pl_mgr.get_playlist_songs(name)
            card  = _PlCard(
                name=name,
                track_count=len(songs),
                cover=self._get_cover(songs),
                on_open=lambda n=name: self._open(n),
                on_delete=None if name == 'Mi Biblioteca' else lambda n=name: self._delete(n),
            )
            self._grid.add_widget(card)

    def _get_cover(self, songs):
        for s in songs:
            c = self._library.get_cover_path(s.get('path',''))
            if c:
                return c
        return None

    def _open(self, name):
        if self._on_open:
            self._on_open(name)

    def _delete(self, name):
        self._pl_mgr.delete_playlist(name)
        self.refresh()

    def _create_dialog(self):
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(12))
        content.add_widget(Label(
            text='Playlist name:',
            color=list(theme.gold), font_size=sp(14),
            size_hint_y=None, height=dp(28),
        ))
        entry = GothicInput(hint_text='My gothic playlist...')
        content.add_widget(entry)

        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        ok  = PrimaryBtn(text='Create')
        can = PrimaryBtn(text='Cancel')
        can.background_color = (0,0,0,0)
        can.color = list(theme.text_sec)
        btn_row.add_widget(ok)
        btn_row.add_widget(can)
        content.add_widget(btn_row)

        popup = Popup(
            title='New Playlist',
            content=content,
            size_hint=(None, None), size=(dp(380), dp(220)),
            background_color=hex_to_rgba(T['surface']),
            title_color=list(theme.gold),
        )

        def do_create(*_):
            name = entry.text.strip()
            if name:
                self._pl_mgr.create_playlist(name)
                self.refresh()
                popup.dismiss()

        ok.bind(on_release=do_create)
        can.bind(on_release=popup.dismiss)
        popup.open()


class _PlCard(BoxLayout):
    def __init__(self, name, track_count, cover, on_open, on_delete, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height      = dp(220)
        self.spacing     = 0

        # Fondo de la tarjeta
        with self.canvas.before:
            self._c_bg_card = Color(*theme.surface[:3], 0.55)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size,
                                        radius=[dp(12)])
            self._c_bd_card = Color(*theme.gold_dark)
            self._bd = Line(rounded_rectangle=(*self.pos, *self.size, dp(12)),
                            width=1.2)
        self.bind(pos=self._upd, size=self._upd)

        # Zona de imagen (portada o placeholder)
        img_box = FloatLayout(size_hint_y=None, height=dp(160))
        with img_box.canvas.before:
            Color(*hex_to_rgba(T['bg_secondary']))
            _ib = RoundedRectangle(pos=img_box.pos, size=img_box.size,
                                   radius=[dp(12), dp(12), 0, 0])
        img_box.bind(pos=lambda w, p: setattr(_ib, 'pos', p),
                     size=lambda w, s: setattr(_ib, 'size', s))

        if cover:
            from kivy.uix.image import Image
            img = Image(source=cover, fit_mode='cover',
                        size_hint=(1,1), pos_hint={'x':0,'y':0})
            img_box.add_widget(img)
        else:
            icon = Label(
                text='[PL]', color=list(theme.gold_muted),
                font_size=sp(30), bold=True,
                pos_hint={'center_x':0.5,'center_y':0.5},
            )
            img_box.add_widget(icon)

        self.add_widget(img_box)

        # Info inferior
        info = BoxLayout(
            orientation='vertical',
            size_hint_y=None, height=dp(60),
            padding=[dp(12), dp(6)], spacing=dp(2),
        )
        with info.canvas.before:
            Color(*theme.surface_light)
            _ib2 = RoundedRectangle(pos=info.pos, size=info.size,
                                    radius=[0, 0, dp(12), dp(12)])
        info.bind(pos=lambda w, p: setattr(_ib2, 'pos', p),
                  size=lambda w, s: setattr(_ib2, 'size', s))

        info.add_widget(Label(
            text=name, color=list(theme.text), font_size=sp(13), bold=True,
            halign='left', size_hint_y=0.55,
        ))
        info.add_widget(Label(
            text=f'n  {track_count} tracks',
            color=list(theme.gold_muted), font_size=sp(11),
            halign='left', size_hint_y=0.45,
        ))
        self.add_widget(info)

        self.bind(on_touch_down=lambda _, t: on_open() if self.collide_point(*t.pos) else None)
        theme.register_widget(self)

    def on_theme_update(self):
        self._c_bg_card.rgba = (*theme.surface[:3], 0.55)
        self._c_bd_card.rgba = list(theme.gold_dark)

    def _upd(self, *_):
        self._bg.pos  = self.pos
        self._bg.size = self.size
        self._bd.rounded_rectangle = (*self.pos, *self.size, dp(12))
