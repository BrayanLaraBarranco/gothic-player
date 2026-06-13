"""
Vista de Descargas — Downloads
URL input funcional + selector de carpeta + formato/calidad + historial
"""
import os
from pathlib import Path
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.utils import platform
from ui.theme import (theme, C_BG, C_SURFACE, C_SURFACE_L, C_SURFACE_H,
                      C_ACCENT, C_ACCENT_H, C_GOLD, C_GOLD_D, C_GOLD_M,
                      C_TEXT, C_TEXT_SEC, C_TEXT_MUT, GothicScrollView, draw_bg)
from ui.widgets import GothicInput, PrimaryBtn, SecondaryBtn, GothicProgress
from ui.header import PageHeader
from modules.downloader import Downloader
from config import app_config, hex_to_rgba, GOTHIC_THEME as T


class DownloadsView(BoxLayout):
    def __init__(self, library, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'
        self._library    = library
        self._tab        = 'active'
        self._completed  = []
        self._dl_folder  = app_config.get_downloads_folder()
        self._downloader = Downloader(self._dl_folder)
        with self.canvas.before:
            self._c_bg = Color(*theme.bg[:3], 0.0)
            self._r_bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd_bg, size=self._upd_bg)
        theme.register_widget(self)
        self._build()

    # ─────────────────────────────────────────────────────────────────────────
    def _upd_bg(self, *_):
        self._r_bg.pos  = self.pos
        self._r_bg.size = self.size

    def on_theme_update(self):
        self._c_bg.rgba = (*theme.bg[:3], 0.0)

    def _build(self):
        self.add_widget(PageHeader(title='Downloads'))

        sv = GothicScrollView()
        inner = BoxLayout(orientation='vertical', size_hint_y=None,
                          spacing=dp(12),
                          padding=[dp(20), dp(12), dp(20), dp(20)])
        inner.bind(minimum_height=inner.setter('height'))
        sv.add_widget(inner)
        self.add_widget(sv)

        # ── Bloque URL ────────────────────────────────────────────────────────
        url_card = _Card()
        url_card.add_widget(_SecLabel('Video / Playlist URL'))

        url_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self._url_input = GothicInput(hint_text='Paste YouTube / SoundCloud URL here...')
        # Asegurar que el input recibe focus correctamente
        self._url_input.write_tab = False
        url_row.add_widget(self._url_input)
        url_card.add_widget(url_row)

        # Fila playlist toggle + paste + download
        action_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        self._pl_btn = _TogBtn('Playlist')
        action_row.add_widget(self._pl_btn)

        paste_btn = SecondaryBtn(text='Paste')
        paste_btn.size_hint = (None, None)
        paste_btn.size      = (dp(80), dp(38))
        paste_btn.bind(on_release=lambda *_: self._paste())
        action_row.add_widget(paste_btn)

        action_row.add_widget(BoxLayout())  # spacer

        dl_btn = PrimaryBtn(text='>>  Download')
        dl_btn.size_hint = (None, None)
        dl_btn.size      = (dp(150), dp(44))
        dl_btn.bind(on_release=lambda *_: self._start_download())
        action_row.add_widget(dl_btn)
        url_card.add_widget(action_row)
        inner.add_widget(url_card)

        # ── Formato + Calidad ─────────────────────────────────────────────────
        fq_card = _Card()
        fq_row  = BoxLayout(size_hint_y=None, height=dp(70), spacing=dp(16))

        fmt_col = BoxLayout(orientation='vertical', spacing=dp(4))
        fmt_col.add_widget(_SecLabel('Format'))
        self._fmt_dd = _DropBtn(
            options=['MP3','FLAC','WAV','OGG','AAC','M4A','OPUS',
                     'MP4','MKV','WEBM','AVI','MOV'],
            default='MP3')
        fmt_col.add_widget(self._fmt_dd)
        fq_row.add_widget(fmt_col)

        qual_col = BoxLayout(orientation='vertical', spacing=dp(4))
        qual_col.add_widget(_SecLabel('Quality'))
        self._qual_dd = _DropBtn(
            options=['BEST','1080P','720P','480P','360P','AUDIO_ONLY'],
            default='BEST')
        qual_col.add_widget(self._qual_dd)
        fq_row.add_widget(qual_col)
        fq_card.add_widget(fq_row)
        inner.add_widget(fq_card)

        # ── Carpeta de destino ────────────────────────────────────────────────
        folder_card = _Card()
        folder_card.add_widget(_SecLabel('Save to folder'))
        folder_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        self._folder_lbl = Label(
            text=self._short_path(self._dl_folder),
            color=list(theme.text_sec), font_size=sp(11),
            halign='left', italic=True,
        )
        self._folder_lbl.bind(
            size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        folder_row.add_widget(self._folder_lbl)
        change_btn = SecondaryBtn(text='Change folder')
        change_btn.size_hint = (None, None)
        change_btn.size      = (dp(140), dp(38))
        change_btn.bind(on_release=lambda *_: self._pick_folder())
        folder_row.add_widget(change_btn)
        folder_card.add_widget(folder_row)
        inner.add_widget(folder_card)

        # ── Barra de estado de descarga ───────────────────────────────────────
        self._status_card = _Card()
        self._status_lbl = Label(
            text='No active downloads',
            color=list(theme.text_muted), font_size=sp(12),
            halign='center', size_hint_y=None, height=dp(28),
        )
        self._status_lbl.bind(
            size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        self._prog = GothicProgress()
        self._status_card.add_widget(self._status_lbl)
        self._status_card.add_widget(self._prog)
        inner.add_widget(self._status_card)

        # ── Tabs activos / completados ────────────────────────────────────────
        tab_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        self._tab_active = _TabBtn('Active (0)', active=True)
        self._tab_done   = _TabBtn('Completed (0)', active=False)
        self._tab_active.bind(on_release=lambda *_: self._switch_tab('active'))
        self._tab_done.bind(on_release=lambda *_: self._switch_tab('done'))
        tab_row.add_widget(self._tab_active)
        tab_row.add_widget(self._tab_done)
        inner.add_widget(tab_row)

        # Lista de descargas completadas
        self._hist_box = BoxLayout(orientation='vertical', size_hint_y=None,
                                   spacing=dp(6))
        self._hist_box.bind(minimum_height=self._hist_box.setter('height'))
        inner.add_widget(self._hist_box)
        self._show_empty()

    # ─────────────────────────────────────────────────────────────────────────
    # Lógica
    # ─────────────────────────────────────────────────────────────────────────
    def _paste(self):
        """Intenta pegar desde el portapapeles."""
        try:
            from kivy.core.clipboard import Clipboard
            txt = Clipboard.paste()
            if txt:
                self._url_input.text = txt.strip()
        except Exception:
            pass

    def _start_download(self):
        url = self._url_input.text.strip()
        if not url:
            self._set_status('Please enter a URL first', error=True)
            return

        fmt = self._fmt_dd.selected.lower()
        # Mapear formato a lo que yt-dlp entiende
        audio_fmts = {'mp3','flac','wav','ogg','aac','m4a','opus'}
        dl_fmt = fmt if fmt in audio_fmts else fmt  # videos pasan tal cual

        self._set_status(f'Starting download ({fmt.upper()})...', color=C_GOLD)
        self._prog.value = 0
        self._url_input.text = ''

        def on_prog(pct):
            Clock.schedule_once(lambda dt: self._upd_prog(pct), 0)

        def on_done(path, title, artist):
            Clock.schedule_once(
                lambda dt: self._on_done(path, title, artist), 0)

        def on_err(msg):
            Clock.schedule_once(
                lambda dt: self._set_status(f'Error: {msg[:80]}', error=True), 0)

        self._downloader.set_download_folder(self._dl_folder)
        self._downloader.download(url, dl_fmt,
                                  on_progress=on_prog,
                                  on_complete=on_done,
                                  on_error=on_err)

    def _upd_prog(self, pct):
        self._prog.value = pct
        self._set_status(f'Downloading... {pct:.0f}%', color=C_GOLD)

    def _on_done(self, path, title, artist):
        self._library.add(path)
        self._completed.append({'path': path, 'title': title, 'artist': artist})
        self._prog.value = 100
        self._set_status(f'Done: {title}', color=C_GOLD)
        n = len(self._completed)
        self._tab_done.set_label(f'Completed ({n})')
        # Actualizar historial si está en tab done
        if self._tab == 'done':
            self._refresh_hist()

    def _set_status(self, text, color=None, error=False):
        self._status_lbl.color = (
            hex_to_rgba(T['error']) if error
            else list(color or C_TEXT_MUT)
        )
        self._status_lbl.text = text

    def _switch_tab(self, tab):
        self._tab = tab
        self._tab_active.set_active(tab == 'active')
        self._tab_done.set_active(tab == 'done')
        self._refresh_hist()

    def _refresh_hist(self):
        self._hist_box.clear_widgets()
        items = self._completed if self._tab == 'done' else []
        if not items:
            self._show_empty()
        else:
            for item in items:
                self._hist_box.add_widget(_DoneRow(
                    item['title'], item['artist']))

    def _show_empty(self):
        self._hist_box.clear_widgets()
        self._hist_box.add_widget(Label(
            text='No downloads yet',
            color=list(theme.text_muted), font_size=sp(13),
            italic=True, halign='center',
            size_hint_y=None, height=dp(48),
        ))

    # ─────────────────────────────────────────────────────────────────────────
    # Selector de carpeta
    # ─────────────────────────────────────────────────────────────────────────
    def _pick_folder(self):
        if platform == 'android':
            self._android_pick_folder()
        else:
            self._desktop_pick_folder()

    def _desktop_pick_folder(self):
        try:
            from tkinter import filedialog, Tk
            root = Tk()
            root.withdraw()
            folder = filedialog.askdirectory(
                title='Select download folder',
                initialdir=str(self._dl_folder),
            )
            root.destroy()
            if folder:
                self._set_folder(folder)
        except Exception as e:
            # Fallback: popup con TextInput
            self._folder_popup()

    def _android_pick_folder(self):
        """En Android muestra un popup para escribir la ruta."""
        self._folder_popup()

    def _folder_popup(self):
        content = BoxLayout(orientation='vertical',
                            padding=dp(16), spacing=dp(10))
        content.add_widget(Label(
            text='Enter folder path:', color=list(theme.gold),
            font_size=sp(13), size_hint_y=None, height=dp(26)))
        entry = GothicInput(text=str(self._dl_folder))
        content.add_widget(entry)
        btn_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        ok  = PrimaryBtn(text='OK')
        can = SecondaryBtn(text='Cancel')
        btn_row.add_widget(ok)
        btn_row.add_widget(can)
        content.add_widget(btn_row)
        popup = Popup(
            title='Download folder',
            content=content,
            size_hint=(None, None), size=(dp(420), dp(200)),
            background_color=hex_to_rgba(T['surface']),
            title_color=list(theme.gold),
        )
        def do_ok(*_):
            folder = entry.text.strip()
            if folder:
                self._set_folder(folder)
            popup.dismiss()
        ok.bind(on_release=do_ok)
        can.bind(on_release=popup.dismiss)
        popup.open()

    def _set_folder(self, folder):
        path = Path(folder)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self._dl_folder = path
        app_config.set_downloads_folder(str(path))
        self._downloader.set_download_folder(path)
        self._folder_lbl.text = self._short_path(path)

    @staticmethod
    def _short_path(p):
        s = str(p)
        return s if len(s) <= 55 else '...' + s[-52:]


# ── Sub-widgets ───────────────────────────────────────────────────────────────
class _Card(BoxLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.spacing     = dp(6)
        self.padding     = [dp(14), dp(10)]
        self.bind(minimum_height=self.setter('height'))
        with self.canvas.before:
            Color(*theme.surface)
            self._r = RoundedRectangle(pos=self.pos, size=self.size,
                                       radius=[dp(12)])
            Color(*theme.gold_dark)
            self._l = Line(rounded_rectangle=(*self.pos, *self.size, dp(12)),
                           width=1.0)
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._r.pos  = self.pos
        self._r.size = self.size
        self._l.rounded_rectangle = (*self.pos, *self.size, dp(12))


def _SecLabel(text):
    lbl = Label(text=text, color=list(theme.gold_muted), font_size=sp(11),
                halign='left', size_hint_y=None, height=dp(20), bold=True)
    lbl.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
    return lbl


class _TabBtn(Button):
    def __init__(self, label, active=False, **kw):
        super().__init__(text=label, **kw)
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.font_size         = sp(12)
        self.bold              = True
        with self.canvas.before:
            self._c = Color(*(theme.accent if active else theme.surface))
            self._r = RoundedRectangle(pos=self.pos, size=self.size,
                                       radius=[dp(8)])
        self.color = list(theme.text if active else theme.text_sec)
        self.bind(pos=self._upd, size=self._upd)

    def set_active(self, val):
        self._c.rgba = list(theme.accent if val else theme.surface)
        self.color   = list(theme.text if val else theme.text_sec)

    def set_label(self, text):
        self.text = text

    def _upd(self, *_):
        self._r.pos  = self.pos
        self._r.size = self.size


class _TogBtn(Button):
    def __init__(self, label, **kw):
        super().__init__(text=label, **kw)
        self._on               = False
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.color             = list(theme.text_sec)
        self.font_size         = sp(12)
        self.size_hint         = (None, None)
        self.size              = (dp(100), dp(38))
        with self.canvas.before:
            self._c = Color(*theme.surface_light)
            self._r = RoundedRectangle(pos=self.pos, size=self.size,
                                       radius=[dp(8)])
            Color(*theme.gold_dark)
            self._l = Line(rounded_rectangle=(*self.pos, *self.size, dp(8)),
                           width=1.0)
        self.bind(pos=self._upd, size=self._upd, on_release=self._tap)

    def _tap(self, *_):
        self._on = not self._on
        self._c.rgba = list(theme.accent if self._on else theme.surface_light)
        self.color   = list(theme.text if self._on else theme.text_sec)

    def _upd(self, *_):
        self._r.pos  = self.pos
        self._r.size = self.size
        self._l.rounded_rectangle = (*self.pos, *self.size, dp(8))

    @property
    def is_on(self):
        return self._on


class _DropBtn(Button):
    """Dropdown gótico funcional via Popup."""
    def __init__(self, options, default, **kw):
        super().__init__(text=default, **kw)
        self.options           = options
        self.selected          = default
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.color             = list(theme.text)
        self.font_size         = sp(13)
        self.bold              = True
        self.size_hint_y       = None
        self.height            = dp(44)
        with self.canvas.before:
            Color(*theme.surface_light)
            self._r = RoundedRectangle(pos=self.pos, size=self.size,
                                       radius=[dp(8)])
            Color(*theme.gold_dark)
            self._l = Line(rounded_rectangle=(*self.pos, *self.size, dp(8)),
                           width=1.0)
        self.bind(pos=self._upd, size=self._upd, on_release=self._open)

    def _upd(self, *_):
        self._r.pos  = self.pos
        self._r.size = self.size
        self._l.rounded_rectangle = (*self.pos, *self.size, dp(8))

    def _open(self, *_):
        sv = ScrollView()
        box = BoxLayout(orientation='vertical', size_hint_y=None,
                        spacing=dp(2), padding=dp(4))
        box.bind(minimum_height=box.setter('height'))
        for opt in self.options:
            b = Button(
                text=opt, size_hint_y=None, height=dp(44),
                background_normal='', background_down='',
                background_color=(0, 0, 0, 0),
                color=list(theme.text), font_size=sp(13), bold=True,
            )
            with b.canvas.before:
                Color(*theme.surface_light)
                _r = RoundedRectangle(pos=b.pos, size=b.size, radius=[dp(6)])
            b.bind(pos=lambda w, p, r=_r: setattr(r, 'pos', p),
                   size=lambda w, s, r=_r: setattr(r, 'size', s))

            def _sel(btn, o=opt):
                self.selected = o
                self.text     = o
                self._popup.dismiss()
            b.bind(on_release=_sel)
            box.add_widget(b)

        sv.add_widget(box)
        self._popup = Popup(
            title=f'Select {self.text}',
            content=sv,
            size_hint=(None, None), size=(dp(260), min(dp(420), dp(60*len(self.options)+40))),
            background_color=hex_to_rgba(T['surface']),
            title_color=list(theme.gold),
        )
        self._popup.open()


class _DoneRow(BoxLayout):
    def __init__(self, title, artist, **kw):
        super().__init__(**kw)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height      = dp(50)
        self.padding     = [dp(12), dp(4)]
        self.spacing     = dp(10)
        with self.canvas.before:
            Color(*theme.surface)
            _r = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
        self.bind(pos=lambda *_: setattr(_r, 'pos', self.pos),
                  size=lambda *_: setattr(_r, 'size', self.size))
        info = BoxLayout(orientation='vertical')
        t = Label(text=title, color=list(theme.text), font_size=sp(12),
                  bold=True, halign='left')
        t.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        a = Label(text=artist, color=list(theme.text_sec), font_size=sp(11),
                  halign='left', italic=True)
        a.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        info.add_widget(t)
        info.add_widget(a)
        self.add_widget(info)
        self.add_widget(Label(text='OK', color=list(theme.gold),
                              font_size=sp(12), bold=True,
                              size_hint=(None, 1), width=dp(36)))
