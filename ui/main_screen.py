"""
Pantalla principal — Gothic Player Pro
El fondo (color + imagen) se dibuja en el canvas de MainScreen.
Todos los layouts internos son TRANSPARENTES para dejar ver el fondo.
"""
import os
from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.floatlayout  import FloatLayout
from kivy.uix.label        import Label
from kivy.uix.button       import Button
from kivy.uix.image        import Image as KivyImage
from kivy.graphics         import Color, Rectangle, Line, RoundedRectangle, Ellipse
from kivy.clock            import Clock
from kivy.metrics          import dp, sp
from kivy.app              import App
from kivy.animation        import Animation

from ui.theme import (C_BG, C_BG2, C_SURFACE, C_SURFACE_L,
                       C_ACCENT, C_GOLD, C_GOLD_D, C_GOLD_M,
                       C_TEXT, C_TEXT_SEC,
                       draw_bg, theme)
from ui.sidebar        import Sidebar
from ui.library_view   import LibraryView
from ui.playlists_view import PlaylistsView
from ui.downloads_view import DownloadsView
from ui.settings_view  import SettingsView
from modules.library          import Library
from modules.playlist_manager import PlaylistManager
from modules.player           import AudioPlayer
from config import (app_config, hex_to_rgba, GOTHIC_THEME as T,
                    AUDIO_EXTENSIONS, VIDEO_EXTENSIONS)


class MainScreen(FloatLayout):
    def __init__(self, **kw):
        super().__init__(**kw)

        # ── Capa 1: color sólido de fondo ─────────────────────────────────────
        with self.canvas.before:
            self._c_bg   = Color(*theme.bg)
            self._r_bg   = Rectangle(pos=self.pos, size=self.size)
            # Capa 2: imagen de fondo (si hay)
            self._c_img  = Color(1, 1, 1, theme.bg_opacity)
            self._r_img  = Rectangle(
                source=theme.bg_image if os.path.isfile(theme.bg_image or '') else '',
                pos=self.pos, size=self.size)
        self.bind(pos=self._upd_bg, size=self._upd_bg)
        theme.register_widget(self)

        self.library  = Library()
        self.pl_mgr   = PlaylistManager()
        self.a_player = AudioPlayer()
        self.a_player.set_volume(app_config.get('volume', 70))

        self._audio_songs   = []
        self._audio_panel   = None
        self._video_overlay = None

        # ── Layout raíz: sidebar | área_central ───────────────────────────────
        # Fondo transparent — la imagen del canvas de MainScreen se ve debajo
        self._root = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 1), pos_hint={'x': 0, 'y': 0},
        )
        self.add_widget(self._root)

        self._sidebar = Sidebar()
        self._sidebar.on_navigate = self._nav
        self._root.add_widget(self._sidebar)

        # Centro: usa FloatLayout para que el overlay de legibilidad quede debajo
        self._center_wrap = FloatLayout()
        self._root.add_widget(self._center_wrap)

        # Overlay oscuro semitransparente sobre el fondo para legibilidad del texto
        # Solo cubre el área central (no el sidebar)
        with self._center_wrap.canvas.before:
            self._c_overlay = Color(0, 0, 0, self._overlay_alpha())
            self._r_overlay = Rectangle(
                pos=self._center_wrap.pos,
                size=self._center_wrap.size)
        self._center_wrap.bind(pos=self._upd_overlay, size=self._upd_overlay)

        self._center = BoxLayout(
            orientation='horizontal',
            size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
        self._center_wrap.add_widget(self._center)

        self._content = BoxLayout(
            orientation='vertical',
            size_hint=(1, 1))
        self._center.add_widget(self._content)

        self._build_views()
        Clock.schedule_once(lambda dt: self._sync(), 0.3)
        self._nav('library')

    # ── Canvas helpers ────────────────────────────────────────────────────────
    def _overlay_alpha(self):
        """Overlay oscuro proporcional a la opacidad de la imagen."""
        if theme.bg_image and os.path.isfile(theme.bg_image or ''):
            # A mayor opacidad de imagen, más overlay para mantener legibilidad
            # Rango: 0.25 (imagen muy suave) a 0.55 (imagen muy visible)
            return 0.05 + (theme.bg_opacity * 0.15)
        return 0.0  # sin imagen → sin overlay, solo color sólido

    def _upd_bg(self, *_):
        self._r_bg.pos  = self.pos
        self._r_bg.size = self.size
        self._r_img.pos  = self.pos
        self._r_img.size = self.size

    def _upd_overlay(self, *_):
        self._r_overlay.pos  = self._center_wrap.pos
        self._r_overlay.size = self._center_wrap.size

    def on_theme_update(self):
        """Llamado por ThemeManager cuando cambia color o imagen."""
        self._c_bg.rgba = list(theme.bg)
        # Actualizar imagen de fondo
        img = theme.bg_image if os.path.isfile(theme.bg_image or '') else ''
        if self._r_img.source != img:
            self._r_img.source = img
        self._c_img.rgba = (1, 1, 1, theme.bg_opacity if img else 0)
        # Actualizar overlay de legibilidad
        self._c_overlay.rgba = (0, 0, 0, self._overlay_alpha())

    # ── Vistas ────────────────────────────────────────────────────────────────
    def _build_views(self):
        self._sv = SettingsView(
            on_vol_change=lambda v: self.a_player.set_volume(int(v)),
            on_theme_change=lambda: None,
        )
        self._views = {
            'library':   LibraryView(library=self.library,
                                     playlist_mgr=self.pl_mgr,
                                     on_play=self._on_play),
            'playlists': PlaylistsView(pl_mgr=self.pl_mgr,
                                       library=self.library,
                                       on_open=self._open_pl),
            'downloads': DownloadsView(library=self.library),
            'settings':  self._sv,
        }

    def _nav(self, key):
        self._content.clear_widgets()
        if key in self._views:
            self._content.add_widget(self._views[key])
        if key == 'library':
            self._views['library'].refresh()
        elif key == 'playlists':
            self._views['playlists'].refresh()

    # ── Reproducción ──────────────────────────────────────────────────────────
    def _on_play(self, fp, meta):
        from pathlib import Path
        if Path(fp).suffix.lower() in VIDEO_EXTENSIONS:
            self._play_video(fp)
        else:
            self._audio_songs = [
                {'path': f, **self.library.get_metadata(f)}
                for f in self.library.get_audio_files()
            ]
            self._show_audio(fp, meta)

    def _show_audio(self, fp, meta):
        if self._audio_panel is not None:
            self._audio_panel.play_song(fp, meta)
            return
        panel = _AudioPanel(
            audio_player=self.a_player,
            library=self.library,
            on_close=self._close_audio,
            on_minimize=self._on_panel_minimize,
            on_expand=self._on_panel_expand,
            size_hint=(None, 1),
            width=0,
        )
        panel.set_playlist_callback(self._audio_nav)
        self._audio_panel = panel
        self._center.add_widget(panel)
        Animation(width=dp(370), duration=0.25, t='out_cubic').start(panel)
        Clock.schedule_once(lambda dt: panel.play_song(fp, meta), 0.1)

    def _on_panel_minimize(self):
        """Mueve el mini player al FloatLayout raíz como barra inferior."""
        panel = self._audio_panel
        if not panel:
            return
        # Quitar del centro
        if panel in self._center.children:
            self._center.remove_widget(panel)
        # Reconfigurar como barra inferior flotante
        panel.size_hint = (1, None)
        panel.height    = dp(72)
        panel.pos_hint  = {'x': 0, 'y': 0}
        panel.y         = 0
        self.add_widget(panel)   # MainScreen es FloatLayout

    def _on_panel_expand(self):
        """Devuelve el panel expandido al centro."""
        panel = self._audio_panel
        if not panel:
            return
        # Quitar del FloatLayout raíz si está ahí
        if panel in self.children:
            self.remove_widget(panel)
        # Limpiar pos_hint y restaurar como columna lateral de altura completa
        panel.pos_hint   = {}
        panel.size_hint  = (None, 1)
        panel.width      = dp(370)
        panel.height     = 0  # será calculado por size_hint_y=1
        self._center.add_widget(panel)

    def _close_audio(self):
        if not self._audio_panel:
            return
        try:
            self.a_player.stop()
        except Exception:
            pass
        panel = self._audio_panel
        self._audio_panel = None

        # Remover del padre correcto (centro o FloatLayout raíz si estaba minimizado)
        if panel in self._center.children:
            self._center.remove_widget(panel)
        elif panel in self.children:
            self.remove_widget(panel)

    def _audio_nav(self, direction):
        songs = self._audio_songs
        if not songs or not self._audio_panel:
            return
        cur = getattr(self._audio_panel, 'current_song', '')
        idx = next((i for i, s in enumerate(songs)
                    if s.get('path') == cur), -1)
        if direction in ('next', 'next_loop'):
            s = songs[(idx + 1) % len(songs)]
        elif direction == 'prev':
            s = songs[max(0, idx - 1)]
        else:
            return
        self._audio_panel.play_song(s['path'], s)

    def _play_video(self, fp):
        from pathlib import Path
        from ui.video_player import VideoPlayerScreen
        self._video_files = self.library.get_video_files()
        self._video_idx   = (self._video_files.index(fp)
                             if fp in self._video_files else 0)
        if self._video_overlay and self._video_overlay in self.children:
            self.remove_widget(self._video_overlay)
        vp = VideoPlayerScreen(
            file_path=fp, title=Path(fp).stem,
            on_close=self._close_video,
            on_prev=lambda: self._vid_skip(-1),
            on_next=lambda: self._vid_skip(1),
            size_hint=(1, 1), pos_hint={'x': 0, 'y': 0},
        )
        self._video_overlay = vp
        self.add_widget(vp)

    def _vid_skip(self, d):
        if not self._video_files:
            return
        self._video_idx = (self._video_idx + d) % len(self._video_files)
        self._play_video(self._video_files[self._video_idx])

    def _close_video(self):
        if self._video_overlay and self._video_overlay in self.children:
            self.remove_widget(self._video_overlay)
        self._video_overlay = None

    def _open_pl(self, name):
        songs = self.pl_mgr.get_playlist_songs(name)
        if songs:
            self._audio_songs = songs
            s = songs[0]
            self._show_audio(s['path'], s)

    def _sync(self):
        for fp in self.library.get_audio_files():
            meta = self.library.get_metadata(fp)
            self.pl_mgr.add_song_to_playlist('Mi Biblioteca', fp, meta)
        if 'library' in self._views:
            self._views['library'].refresh()

    def on_pause(self):  return True
    def on_resume(self): pass


# ── _AudioPanel ───────────────────────────────────────────────────────────────
class _AudioPanel(BoxLayout):
    """
    EXPANDIDO  → columna derecha (size_hint=(None,1), width=370dp)
    MINIMIZADO → barra inferior flotante (size_hint=(1,None), height=72dp)
                 Gestionado por MainScreen._on_panel_minimize/expand
    """
    FULL_W = 370

    def __init__(self, audio_player, library, on_close,
                 on_minimize=None, on_expand=None, **kw):
        super().__init__(**kw)
        self.orientation  = 'vertical'
        self._minimized   = False
        self._on_close    = on_close
        self._on_minimize = on_minimize
        self._on_expand   = on_expand

        with self.canvas.before:
            self._c_bg  = Color(*theme.bg2[:3], 0.45)
            self._bg    = Rectangle(pos=self.pos, size=self.size)
            self._c_brd = Color(*theme.gold_dark)
            self._brd   = Line(points=[self.x, self.y, self.x, self.top],
                               width=1.8)
        self.bind(pos=self._upd, size=self._upd)
        theme.register_widget(self)

        # ── Header (modo expandido) ────────────────────────────────────────
        self._hdr = BoxLayout(size_hint_y=None, height=dp(40),
                              padding=[dp(14), dp(6)], spacing=dp(6))
        with self._hdr.canvas.before:
            self._c_hdr = Color(*theme.bg[:3], 0.60)
            self._r_hdr = Rectangle(pos=self._hdr.pos, size=self._hdr.size)
            self._c_hln = Color(*theme.gold_dark)
            self._r_hln = Line(
                points=[self._hdr.x, self._hdr.y,
                        self._hdr.right, self._hdr.y], width=1.0)
        self._hdr.bind(pos=self._upd_hdr, size=self._upd_hdr)

        self._np_lbl = Label(
            text='NOW PLAYING', color=list(theme.gold),
            font_size=sp(10), bold=True, halign='left')
        self._hdr.add_widget(self._np_lbl)
        self._hdr.add_widget(BoxLayout())

        self._min_btn = _HeaderBtn('–', self._toggle_minimize,
                                   bg_color=theme.surface)
        self._hdr.add_widget(self._min_btn)
        self._close_btn = _HeaderBtn('✕', on_close, bg_color=theme.accent)
        self._hdr.add_widget(self._close_btn)
        self.add_widget(self._hdr)

        # ── Widget de reproducción ─────────────────────────────────────────
        from ui.audio_player_widget import AudioPlayerWidget
        self._aw = AudioPlayerWidget(audio_player=audio_player, library=library)
        self.add_widget(self._aw)

        # ── Mini player (barra inferior) — inicialmente oculto ─────────────
        self._mini = _MiniBar(
            audio_widget=self._aw,
            on_expand=self._toggle_minimize,
            on_close=on_close)
        self._mini.opacity     = 0
        self._mini.size_hint_y = None
        self._mini.height      = 0
        self.add_widget(self._mini)

    # ── Toggle ────────────────────────────────────────────────────────────
    def _toggle_minimize(self):
        if not self._minimized:
            self._do_minimize()
        else:
            self._do_expand()

    def _do_minimize(self):
        self._minimized = True
        # Ocultar header y reproductor
        self._hdr.opacity     = 0
        self._hdr.size_hint_y = None
        self._hdr.height      = 0
        self._aw.opacity      = 0
        self._aw.size_hint_y  = None
        self._aw.height       = 0
        # Mostrar mini bar
        self._mini.height      = dp(72)
        self._mini.opacity     = 1
        self._mini.update_info(
            self._aw.current_title,
            self._aw.current_artist,
            self._aw._library.get_cover_path(self._aw.current_song) or '')
        # Notificar a MainScreen para mover este widget
        if self._on_minimize:
            self._on_minimize()

    def _do_expand(self):
        self._minimized = False
        # Ocultar mini bar
        self._mini.opacity     = 0
        self._mini.size_hint_y = None
        self._mini.height      = 0
        # Mostrar header y reproductor
        self._hdr.size_hint_y = None
        self._hdr.height      = dp(40)
        self._hdr.opacity     = 1
        self._aw.size_hint_y  = 1
        self._aw.opacity      = 1
        # Notificar a MainScreen para devolver al layout
        if self._on_expand:
            self._on_expand()

    # ── Canvas ────────────────────────────────────────────────────────────
    def _upd(self, *_):
        self._bg.pos     = self.pos
        self._bg.size    = self.size
        self._brd.points = [self.x, self.y, self.x, self.top]

    def _upd_hdr(self, w, *_):
        self._r_hdr.pos    = w.pos
        self._r_hdr.size   = w.size
        self._r_hln.points = [w.x, w.y, w.right, w.y]

    def on_theme_update(self):
        self._c_bg.rgba    = (*theme.bg2[:3], 0.45)
        self._c_brd.rgba   = list(theme.gold_dark)
        self._c_hdr.rgba   = (*theme.bg[:3], 0.60)
        self._c_hln.rgba   = list(theme.gold_dark)
        self._np_lbl.color = list(theme.gold)

    def play_song(self, fp, meta):
        if self._minimized:
            self._mini.update_info(
                meta.get('title', ''),
                meta.get('artist', ''),
                self._aw._library.get_cover_path(fp) or '')
        self._aw.play_song(fp, meta)

    def set_playlist_callback(self, cb):
        self._aw.set_playlist_callback(cb)

    @property
    def current_song(self):
        return self._aw.current_song


# ── _HeaderBtn ────────────────────────────────────────────────────────────────
class _HeaderBtn(Button):
    def __init__(self, txt, cb, bg_color=None, **kw):
        super().__init__(text=txt, **kw)
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.color             = list(theme.gold)
        self.font_size         = sp(13)
        self.bold              = True
        self.size_hint         = (None, None)
        self.size              = (dp(28), dp(28))
        with self.canvas.before:
            self._c_bg = Color(*(bg_color or theme.surface))
            self._r_bg = RoundedRectangle(pos=self.pos, size=self.size,
                                          radius=[dp(14)])
        self.bind(pos=self._upd, size=self._upd,
                  on_release=lambda *_: cb())

    def _upd(self, *_):
        self._r_bg.pos  = self.pos
        self._r_bg.size = self.size

    def on_theme_update(self): pass


# ── _MiniBar — barra horizontal inferior ──────────────────────────────────────
class _MiniBar(BoxLayout):
    """
    [portada 56x56] [título\nartista] [espaciador] [|<] [▶/II] [>|] [✕]
    Idéntico a imagen 1 de referencia.
    """
    def __init__(self, audio_widget, on_expand, on_close, **kw):
        super().__init__(**kw)
        self.orientation = 'horizontal'
        self.spacing     = dp(8)
        self.padding     = [dp(10), dp(8), dp(10), dp(8)]
        self._aw         = audio_widget

        with self.canvas.before:
            self._c_bg  = Color(*theme.bg2[:3], 0.88)
            self._r_bg  = Rectangle(pos=self.pos, size=self.size)
            self._c_top = Color(*theme.gold_dark)
            self._r_top = Line(
                points=[self.x, self.top, self.right, self.top], width=1.8)
        self.bind(pos=self._upd, size=self._upd)
        theme.register_widget(self)

        # Portada clickeable → expande
        self._cover_btn = _MiniCoverBtn()
        self._cover_btn.bind(on_release=lambda *_: on_expand())
        self.add_widget(self._cover_btn)

        # Info textual — toda el área es clickeable para expandir
        info = _ExpandBtn(on_expand=on_expand)
        self._t = Label(text='Sin título',
                        color=(1.0, 0.96, 0.88, 1.0),
                        font_size=sp(13), bold=True, halign='left',
                        shorten=True, shorten_from='right')
        self._t.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        self._a = Label(text='',
                        color=list(theme.gold_muted),
                        font_size=sp(10), italic=True, halign='left',
                        shorten=True, shorten_from='right')
        self._a.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        info.add_widget(self._t)
        info.add_widget(self._a)
        self.add_widget(info)

        self.add_widget(BoxLayout())  # spacer empuja controles a la derecha

        # Controles: prev, play/pause, next, cerrar
        self._b_prev = _MiniCtrl('|<', lambda *_: audio_widget._prev())
        self._b_play = _MiniCtrl(' >', None)
        self._b_play.bind(on_release=lambda *_: self._play_toggle())
        self._b_next = _MiniCtrl('>|', lambda *_: audio_widget._next())
        self._b_x    = _MiniCtrl('✕', on_close, close=True)

        for b in (self._b_prev, self._b_play, self._b_next, self._b_x):
            self.add_widget(b)

    def _play_toggle(self):
        self._aw._toggle()
        self._b_play.text = 'II' if self._aw.is_playing else ' >'

    def update_info(self, title, artist, cover):
        self._t.text = title  or 'Sin título'
        self._a.text = artist or ''
        self._cover_btn.set_source(cover)
        self._b_play.text = 'II' if self._aw.is_playing else ' >'

    def _upd(self, *_):
        self._r_bg.pos    = self.pos
        self._r_bg.size   = self.size
        self._r_top.points = [self.x, self.top, self.right, self.top]

    def on_theme_update(self):
        self._c_bg.rgba  = (*theme.bg2[:3], 0.88)
        self._c_top.rgba = list(theme.gold_dark)
        self._t.color    = (1.0, 0.96, 0.88, 1.0)
        self._a.color    = list(theme.gold_muted)


class _MiniCoverBtn(Button):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.text              = ''
        self.size_hint         = (None, 1)
        self.width             = dp(54)
        self._img = KivyImage(
            source='', fit_mode='cover',
            size_hint=(None, None), size=(dp(50), dp(50)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5})
        with self._img.canvas.after:
            Color(*theme.gold_dark)
            self._bd = Line(
                rounded_rectangle=(self._img.x, self._img.y,
                                   self._img.width, self._img.height, dp(4)),
                width=1.2)
        self._img.bind(
            pos=lambda w, p: setattr(self._bd, 'rounded_rectangle',
                                     (*p, *w.size, dp(4))),
            size=lambda w, s: setattr(self._bd, 'rounded_rectangle',
                                      (*w.pos, *s, dp(4))))
        self.add_widget(self._img)

    def set_source(self, path):
        import os as _os
        if path and _os.path.isfile(path):
            self._img.source = path
            self._img.reload()
        else:
            self._img.source = ''




# ── _ExpandBtn — área clickeable que expande el mini player ──────────────────
class _ExpandBtn(BoxLayout):
    """BoxLayout que captura toques y llama on_expand."""
    def __init__(self, on_expand, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'
        self.spacing     = dp(1)
        self._on_expand  = on_expand

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._on_expand()
            return True
        return super().on_touch_down(touch)

class _MiniCtrl(Button):
    def __init__(self, txt, cb=None, accent=False, close=False, **kw):
        super().__init__(text=txt, **kw)
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.font_size         = sp(14)
        self.bold              = True
        self.size_hint         = (None, 1)
        self.width             = dp(44)
        self._close            = close

        if close:
            # X: fondo transparente, texto blanco, contorno ligeramente resaltado
            self.color   = (1.0, 1.0, 1.0, 1.0)
            fill         = (0.0, 0.0, 0.0, 0.0)
            border_color = (1.0, 0.85, 0.85, 0.85)
        elif accent:
            self.color     = list(theme.gold)
            fill           = list(theme.accent)
            border_color   = list(theme.gold_dark)
        else:
            self.color     = list(theme.gold)
            fill           = (*theme.surface[:3], 0.55)
            border_color   = list(theme.gold_dark)

        with self.canvas.before:
            self._c_f = Color(*fill)
            self._r_f = Ellipse(pos=self.pos, size=self.size)
            self._c_b = Color(*border_color)
            self._r_b = Line(ellipse=(*self.pos, *self.size), width=1.8 if close else 1.0)
        self.bind(pos=self._upd, size=self._upd)
        if cb: self.bind(on_release=lambda *_: cb())
        theme.register_widget(self)

    def _upd(self, *_):
        self._r_f.pos     = self.pos
        self._r_f.size    = self.size
        self._r_b.ellipse = (*self.pos, *self.size)

    def on_theme_update(self):
        if not self._close:
            self._c_b.rgba = list(theme.gold_dark)

