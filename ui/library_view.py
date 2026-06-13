"""
Vista de Biblioteca — Library
Todos los widgets se registran en ThemeManager para actualizarse en tiempo real.
"""
from pathlib import Path
from kivy.uix.boxlayout  import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label       import Label
from kivy.uix.button      import Button
from kivy.graphics        import Color, Rectangle, RoundedRectangle, Line
from kivy.clock           import Clock
from kivy.metrics         import dp, sp
from ui.theme  import (theme, draw_bg,
                        C_BG, C_SURFACE, C_SURFACE_L, C_SURFACE_H,
                        C_ACCENT, C_GOLD, C_GOLD_D, C_GOLD_M,
                        C_TEXT, C_TEXT_SEC, C_TEXT_MUT,
                        GothicScrollView)
from ui.widgets import GothicInput, PrimaryBtn, SecondaryBtn, GothicCard, GothicSep
from ui.header  import PageHeader
from modules.utils import format_time, truncate_text
from config import hex_to_rgba, GOTHIC_THEME as T


class LibraryView(BoxLayout):
    def __init__(self, library, playlist_mgr, on_play=None, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'
        self._library    = library
        self._pl_mgr     = playlist_mgr
        self._on_play    = on_play
        self._filter     = 'all'
        self._search_q   = ''
        with self.canvas.before:
            self._c_bg = Color(*theme.bg[:3], 0.0)
            self._r_bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd_bg, size=self._upd_bg)
        self._build()
        Clock.schedule_once(lambda dt: self._refresh(), 0.1)
        theme.register_widget(self)

    def _upd_bg(self, *_):
        self._r_bg.pos  = self.pos
        self._r_bg.size = self.size

    def on_theme_update(self):
        self._c_bg.rgba = (*theme.bg[:3], 0.0)
        # Actualizar filtros y lista visibles
        for k, btn in self._f_btns.items():
            btn.on_theme_update()
        self._count_lbl.color = list(theme.text_muted)

    def _build(self):
        self.add_widget(PageHeader(title='Library'))

        search_box = BoxLayout(size_hint_y=None, height=dp(56),
                               padding=[dp(20), dp(6)])
        self._search = GothicInput(hint_text='Search your library...')
        self._search.bind(text=self._on_search)
        search_box.add_widget(self._search)
        self.add_widget(search_box)

        filt_row = BoxLayout(size_hint_y=None, height=dp(48),
                             padding=[dp(20), 0, dp(20), dp(8)], spacing=dp(4))
        self._f_btns = {}
        for key, label in [('all', 'All'), ('audio', 'Audio'), ('video', 'Video')]:
            btn = _FilterBtn(label, active=(key == 'all'))
            btn.bind(on_release=lambda b, k=key: self._set_filter(k))
            self._f_btns[key] = btn
            filt_row.add_widget(btn)
        self.add_widget(filt_row)

        info_row = BoxLayout(size_hint_y=None, height=dp(36),
                             padding=[dp(20), 0, dp(20), 0])
        self._count_lbl = Label(text='0 items', color=list(theme.text_muted),
                                font_size=sp(12), halign='left')
        self._count_lbl.bind(
            size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        info_row.add_widget(self._count_lbl)
        sort_btn = SecondaryBtn(text='Sort: title',
                                size_hint=(None, None),
                                size=(dp(110), dp(30)))
        info_row.add_widget(sort_btn)
        self.add_widget(info_row)

        self._list_sv  = GothicScrollView()
        self._list_box = BoxLayout(orientation='vertical', size_hint_y=None,
                                   spacing=dp(2),
                                   padding=[dp(20), dp(4), dp(20), dp(20)])
        self._list_box.bind(minimum_height=self._list_box.setter('height'))
        self._list_sv.add_widget(self._list_box)
        self.add_widget(self._list_sv)

    # ── Actualizar ─────────────────────────────────────────────────────────────
    def refresh(self):
        self._refresh()

    def _refresh(self):
        q = self._search_q.lower()
        files = self._library.search(q) if q else self._library.get_all()

        if self._filter == 'audio':
            from config import AUDIO_EXTENSIONS
            files = [f for f in files
                     if Path(f).suffix.lower() in AUDIO_EXTENSIONS]
        elif self._filter == 'video':
            from config import VIDEO_EXTENSIONS
            files = [f for f in files
                     if Path(f).suffix.lower() in VIDEO_EXTENSIONS]

        self._list_box.clear_widgets()
        self._count_lbl.text = f'{len(files)} items'

        if not files:
            self._list_box.add_widget(_EmptyState())
            return

        for i, fp in enumerate(files):
            meta = self._library.get_metadata(fp)
            row  = _SongRow(
                index=i + 1,
                file_path=fp,
                title=meta.get('title', Path(fp).stem),
                artist=meta.get('artist', 'Unknown'),
                duration=format_time(meta.get('duration', 0)),
                cover=self._library.get_cover_path(fp),
                on_play=lambda f=fp, m=meta: self._play(f, m),
                on_remove=lambda f=fp: self._remove(f),
            )
            self._list_box.add_widget(row)

    def _play(self, fp, meta):
        if self._on_play:
            self._on_play(fp, meta)

    def _remove(self, fp):
        self._library.remove(fp)
        self._refresh()

    def _on_search(self, _, text):
        self._search_q = text
        Clock.schedule_once(lambda dt: self._refresh(), 0.3)

    def _set_filter(self, key):
        self._filter = key
        for k, btn in self._f_btns.items():
            btn.set_active(k == key)
        self._refresh()

    def add_files(self, file_paths):
        for fp in file_paths:
            self._library.add(fp)
            meta = self._library.get_metadata(fp)
            self._pl_mgr.add_song_to_playlist('Mi Biblioteca', fp, meta)
        self._refresh()


# ── _SongRow ──────────────────────────────────────────────────────────────────
class _SongRow(BoxLayout):
    def __init__(self, index, file_path, title, artist, duration,
                 cover, on_play, on_remove, **kw):
        super().__init__(**kw)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height      = dp(60)
        self.padding     = [dp(12), dp(4)]
        self.spacing     = dp(10)

        with self.canvas.before:
            self._c_bg = Color(*theme.surface[:3], 0.38)
            self._bg   = RoundedRectangle(pos=self.pos, size=self.size,
                                          radius=[dp(8)])

        self.bind(pos=self._upd, size=self._upd)
        theme.register_widget(self)

        self._num_lbl = Label(
            text=f'{index:02d}', color=list(theme.text_muted),
            font_size=sp(12), bold=True,
            size_hint=(None, 1), width=dp(30), halign='center')
        self.add_widget(self._num_lbl)

        cov = _MiniCover(source=cover or '', size_hint=(None, 1), width=dp(44))
        self.add_widget(cov)

        info = BoxLayout(orientation='vertical', spacing=dp(2))
        self._t_lbl = Label(
            text=truncate_text(title, 45),
            color=[1.0, 0.96, 0.88, 1.0], font_size=sp(13), bold=True,
            halign='left', size_hint_y=0.55)
        self._t_lbl.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        self._a_lbl = Label(
            text=truncate_text(artist, 50),
            color=list(theme.gold_muted), font_size=sp(11),
            halign='left', italic=True, size_hint_y=0.45)
        self._a_lbl.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        info.add_widget(self._t_lbl)
        info.add_widget(self._a_lbl)
        self.add_widget(info)

        self._dur_lbl = Label(
            text=duration, color=list(theme.gold_muted),
            font_size=sp(11), size_hint=(None, 1), width=dp(46), halign='right')
        self.add_widget(self._dur_lbl)

        pb = _IconBtn('>', on_press=lambda *_: on_play())
        self.add_widget(pb)

    def _upd(self, *_):
        self._bg.pos  = self.pos
        self._bg.size = self.size


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._c_bg.rgba = (*theme.get('surface_hover')[:3], 0.85)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        self._c_bg.rgba = (*theme.surface[:3], 0.45)
        return super().on_touch_up(touch)

    def on_theme_update(self):
        self._c_bg.rgba      = (*theme.surface[:3], 0.45)
        self._t_lbl.color    = [1.0, 0.96, 0.88, 1.0]
        self._a_lbl.color    = list(theme.gold_muted)
        self._num_lbl.color  = list(theme.text_muted)
        self._dur_lbl.color  = list(theme.gold_muted)


# ── _MiniCover ────────────────────────────────────────────────────────────────
_IMG_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}

class _MiniCover(BoxLayout):
    def __init__(self, source='', **kw):
        super().__init__(**kw)
        with self.canvas.before:
            self._c_bg = Color(*theme.bg2[:3], 0.50)
            self._bg   = RoundedRectangle(pos=self.pos, size=self.size,
                                          radius=[dp(4)])
        self.bind(pos=self._upd, size=self._upd)
        theme.register_widget(self)
        # Solo cargar si es una imagen real (no un video/audio)
        from pathlib import Path as _P
        is_image = (source and
                    _P(source).suffix.lower() in _IMG_EXTS and
                    _P(source).exists())
        if is_image:
            from kivy.uix.image import Image
            self._lbl = None
            self.add_widget(Image(source=source, fit_mode='contain'))
        else:
            self._lbl = Label(text='♪', color=list(theme.gold_muted),
                              font_size=sp(18), bold=True)
            self.add_widget(self._lbl)

    def _upd(self, *_):
        self._bg.pos  = self.pos
        self._bg.size = self.size

    def on_theme_update(self):
        self._c_bg.rgba = (*theme.bg2[:3], 0.50)
        if hasattr(self, '_lbl'):
            self._lbl.color = list(theme.gold_muted)


# ── _IconBtn (botón play circular) ────────────────────────────────────────────
class _IconBtn(Button):
    def __init__(self, text='>', **kw):
        super().__init__(text=text, **kw)
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.color             = list(theme.gold)
        self.font_size         = sp(16)
        self.bold              = True
        self.size_hint         = (None, None)
        self.size              = (dp(38), dp(38))
        with self.canvas.before:
            self._c_bg = Color(*theme.accent)
            self._bg   = RoundedRectangle(pos=self.pos, size=self.size,
                                          radius=[dp(19)])
        self.bind(pos=self._upd, size=self._upd, state=self._on_st)
        theme.register_widget(self)

    def _upd(self, *_):
        self._bg.pos  = self.pos
        self._bg.size = self.size

    def _on_st(self, *_):
        self._c_bg.rgba = list(theme.accent_hover if self.state == 'down'
                               else theme.accent)

    def on_theme_update(self):
        self._c_bg.rgba = list(theme.accent)
        self.color      = list(theme.gold)


# ── _FilterBtn ────────────────────────────────────────────────────────────────
class _FilterBtn(Button):
    def __init__(self, label, active=False, **kw):
        super().__init__(text=label, **kw)
        self._active           = active
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.font_size         = sp(13)
        self.bold              = True
        with self.canvas.before:
            self._c_fill = Color(*(theme.accent if active else (*theme.surface[:3], 0.45)))
            self._r_fill = RoundedRectangle(pos=self.pos, size=self.size,
                                            radius=[dp(8)])
        self.color = list(theme.text if active else theme.text_sec)
        self.bind(pos=self._upd, size=self._upd)
        theme.register_widget(self)

    def set_active(self, val):
        self._active          = val
        self._c_fill.rgba     = list(theme.accent) if val else (*theme.surface[:3], 0.45)
        self.color            = list(theme.text   if val else theme.text_sec)

    def _upd(self, *_):
        self._r_fill.pos  = self.pos
        self._r_fill.size = self.size

    def on_theme_update(self):
        self._c_fill.rgba = list(theme.accent) if self._active else (*theme.surface[:3], 0.45)
        self.color        = list(theme.text   if self._active else theme.text_sec)


# ── _EmptyState ───────────────────────────────────────────────────────────────
class _EmptyState(BoxLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height      = dp(300)
        self.padding     = dp(40)
        self.spacing     = dp(12)
        self._icon = Label(text='~', color=list(theme.gold_muted),
                           font_size=sp(48), bold=True,
                           size_hint_y=None, height=dp(80))
        self._h1   = Label(text='Your Library is Empty',
                           color=list(theme.text), font_size=sp(18), bold=True,
                           halign='center', size_hint_y=None, height=dp(30))
        self._h2   = Label(
            text='Download some music or videos to get started',
            color=list(theme.text_sec), font_size=sp(13),
            halign='center', italic=True, size_hint_y=None, height=dp(24))
        for w in (self._icon, self._h1, self._h2):
            self.add_widget(w)
        theme.register_widget(self)

    def on_theme_update(self):
        self._icon.color = list(theme.gold_muted)
        self._h1.color   = list(theme.text)
        self._h2.color   = list(theme.text_sec)
