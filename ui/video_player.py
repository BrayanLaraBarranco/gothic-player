"""
Reproductor de Video — Gothic Player Pro
Usa ffpyplayer directamente via kivy.core.video para máxima compatibilidad
en Windows, Linux y macOS. Estilo Netflix/YouTube con controles overlay.
"""
import os
import time as _time
from kivy.uix.floatlayout  import FloatLayout
from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.label        import Label
from kivy.uix.button       import Button
from kivy.uix.slider       import Slider
from kivy.uix.image        import Image as KivyImage
from kivy.graphics         import (Color, Rectangle, RoundedRectangle,
                                    Line, Ellipse)
from kivy.graphics.texture import Texture
from kivy.clock            import Clock
from kivy.metrics          import dp, sp
from kivy.animation        import Animation
from kivy.properties       import ObjectProperty

from ui.theme   import (C_GOLD, C_GOLD_D, C_GOLD_M, C_ACCENT, C_ACCENT_H,
                         C_TEXT, C_TEXT_SEC, C_TEXT_MUT,
                         C_SEEK_BG, C_SEEK_FILL, C_SEEK_THUMB)
from modules.utils import format_time
from config import hex_to_rgba, GOTHIC_THEME as T


# ── SeekBar de video ──────────────────────────────────────────────────────────
class _VSeek(FloatLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint_y = None
        self.height      = dp(24)
        self._prog       = 0.0
        self._drag       = False
        self.on_seek     = None
        self.bind(pos=self._rd, size=self._rd)

    def _rd(self, *_):
        self.canvas.clear()
        w, h, x, y = self.width, self.height, self.x, self.y
        if w <= 0:
            return
        th = dp(5)
        ty = y + (h - th) / 2
        with self.canvas:
            Color(*C_SEEK_BG)
            RoundedRectangle(pos=(x, ty), size=(w, th), radius=[th / 2])
            fw = w * self._prog
            if fw > 0:
                Color(*C_SEEK_FILL)
                RoundedRectangle(pos=(x, ty), size=(fw, th), radius=[th / 2])
            tx = x + fw
            tr = dp(9)
            Color(*C_SEEK_THUMB)
            Ellipse(pos=(tx - tr, y + h / 2 - tr), size=(tr * 2, tr * 2))
            Color(*C_GOLD_D)
            Line(circle=(tx, y + h / 2, tr - dp(1)), width=1.4)

    def set_progress(self, v):
        self._prog = max(0.0, min(1.0, v))
        self._rd()

    def on_touch_down(self, t):
        if self.collide_point(*t.pos):
            self._drag = True
            self._go(t.x)
            return True
        return super().on_touch_down(t)

    def on_touch_move(self, t):
        if self._drag:
            self._go(t.x)
            return True
        return super().on_touch_move(t)

    def on_touch_up(self, t):
        if self._drag:
            self._drag = False
            self._go(t.x)
            return True
        return super().on_touch_up(t)

    def _go(self, tx):
        if self.width > 0:
            v = max(0.0, min(1.0, (tx - self.x) / self.width))
            self._prog = v
            self._rd()
            if self.on_seek:
                self.on_seek(v)


# ── Slider de volumen ─────────────────────────────────────────────────────────
class _VVol(Slider):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.cursor_image = ''
        self.cursor_size  = (1, 1)
        self.bind(pos=self._rd, size=self._rd, value=self._rd)

    def _rd(self, *_):
        self.canvas.after.clear()
        with self.canvas.after:
            y  = self.center_y
            x0 = self.x + dp(4)
            tw = self.width - dp(8)
            h  = dp(4)
            Color(*C_SEEK_BG)
            RoundedRectangle(pos=(x0, y - h / 2), size=(tw, h), radius=[h / 2])
            r = ((self.value - self.min) / (self.max - self.min)
                 if self.max > self.min else 0)
            if r > 0:
                Color(*C_SEEK_FILL)
                RoundedRectangle(pos=(x0, y - h / 2), size=(tw * r, h),
                                 radius=[h / 2])
            tx = x0 + tw * r
            tr = dp(7)
            Color(*C_SEEK_THUMB)
            Ellipse(pos=(tx - tr, y - tr), size=(tr * 2, tr * 2))


# ── Botón de control ──────────────────────────────────────────────────────────
class _VBtn(Button):
    def __init__(self, txt, sz=dp(44), primary=False, **kw):
        super().__init__(text=txt, **kw)
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.color             = list(C_GOLD)
        self.font_size         = sp(20) if primary else sp(13)
        self.bold              = True
        self.size_hint         = (None, None)
        self.size              = (sz, sz)
        if primary:
            with self.canvas.before:
                self._c_bg = Color(*C_ACCENT)
                self._r_bg = RoundedRectangle(pos=self.pos, size=self.size,
                                              radius=[sz / 2])
            self.bind(pos=self._upd, size=self._upd, state=self._st)

    def _upd(self, *_):
        if hasattr(self, '_r_bg'):
            self._r_bg.pos  = self.pos
            self._r_bg.size = self.size

    def _st(self, *_):
        if hasattr(self, '_c_bg'):
            self._c_bg.rgba = list(
                C_ACCENT_H if self.state == 'down' else C_ACCENT)


# ── Overlay de controles estilo YouTube ───────────────────────────────────────
class _YTControls(FloatLayout):
    def __init__(self, title='', **kw):
        super().__init__(**kw)

        # Gradiente superior
        top = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(68),
            pos_hint={'x': 0, 'top': 1},
            padding=[dp(16), dp(14), dp(16), dp(8)],
            spacing=dp(10),
        )
        with top.canvas.before:
            Color(0, 0, 0, 0.82)
            self._top_bg = Rectangle(pos=top.pos, size=top.size)
        top.bind(pos=lambda w, p: setattr(self._top_bg, 'pos', p),
                 size=lambda w, s: setattr(self._top_bg, 'size', s))

        self._lbl_title = Label(
            text=title, color=list(C_TEXT),
            font_size=sp(15), bold=True, halign='left',
        )
        self._lbl_title.bind(
            size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        top.add_widget(self._lbl_title)

        self._btn_close = _VBtn('X', sz=dp(40))
        with self._btn_close.canvas.before:
            Color(*C_ACCENT)
            _cr = RoundedRectangle(pos=self._btn_close.pos,
                                   size=self._btn_close.size, radius=[dp(20)])
        self._btn_close.bind(
            pos=lambda w, p: setattr(_cr, 'pos', p),
            size=lambda w, s: setattr(_cr, 'size', s))
        top.add_widget(self._btn_close)
        self.add_widget(top)

        # Indicador skip central
        self._skip_lbl = Label(
            text='', color=list(C_GOLD),
            font_size=sp(26), bold=True, halign='center',
            size_hint=(None, None), size=(dp(140), dp(60)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            opacity=0,
        )
        self.add_widget(self._skip_lbl)

        # Barra inferior
        bot = BoxLayout(
            orientation='vertical',
            size_hint=(1, None), height=dp(116),
            pos_hint={'x': 0, 'y': 0},
            padding=[dp(16), dp(6), dp(16), dp(12)],
            spacing=dp(2),
        )
        with bot.canvas.before:
            Color(0, 0, 0, 0.82)
            self._bot_bg = Rectangle(pos=bot.pos, size=bot.size)
        bot.bind(pos=lambda w, p: setattr(self._bot_bg, 'pos', p),
                 size=lambda w, s: setattr(self._bot_bg, 'size', s))

        # Seekbar + tiempos
        seek_row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(8))
        self._lbl_pos = Label(text='0:00', color=list(C_GOLD_M),
                              font_size=sp(12), size_hint=(None, 1),
                              width=dp(44), halign='right')
        self._seek = _VSeek()
        self._lbl_dur = Label(text='0:00', color=list(C_GOLD_M),
                              font_size=sp(12), size_hint=(None, 1),
                              width=dp(44), halign='left')
        seek_row.add_widget(self._lbl_pos)
        seek_row.add_widget(self._seek)
        seek_row.add_widget(self._lbl_dur)
        bot.add_widget(seek_row)

        # Botones
        ctrl = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(6))
        self._btn_prev = _VBtn('|<', sz=dp(40))
        self._btn_rew  = _VBtn('-10', sz=dp(46))
        self._btn_play = _VBtn(' >', sz=dp(58), primary=True)
        self._btn_ff   = _VBtn('+10', sz=dp(46))
        self._btn_next = _VBtn('>|', sz=dp(40))
        sp_box = BoxLayout()

        # Volumen
        vol_box = BoxLayout(size_hint=(None, 1), width=dp(160), spacing=dp(6))
        vol_box.add_widget(Label(text='Vol', color=list(C_GOLD_M),
                                 font_size=sp(11), size_hint=(None, 1),
                                 width=dp(28)))
        self._vol = _VVol(min=0, max=100, value=80)
        vol_box.add_widget(self._vol)
        self._lbl_vol = Label(text='80%', color=list(C_GOLD_M),
                              font_size=sp(11), size_hint=(None, 1),
                              width=dp(38))
        vol_box.add_widget(self._lbl_vol)

        for w in (self._btn_prev, self._btn_rew, self._btn_play,
                  self._btn_ff, self._btn_next, sp_box, vol_box):
            ctrl.add_widget(w)
        bot.add_widget(ctrl)
        self.add_widget(bot)

    def wire(self, play_cb, prev_cb, next_cb, rew_cb, ff_cb,
             seek_cb, vol_cb, close_cb):
        self._btn_play.bind(on_release=lambda *_: play_cb())
        self._btn_prev.bind(on_release=lambda *_: prev_cb())
        self._btn_next.bind(on_release=lambda *_: next_cb())
        self._btn_rew.bind(on_release=lambda *_: rew_cb())
        self._btn_ff.bind(on_release=lambda *_: ff_cb())
        self._btn_close.bind(on_release=lambda *_: close_cb())
        self._seek.on_seek = seek_cb
        self._vol.bind(value=lambda _, v: (
            setattr(self._lbl_vol, 'text', f'{int(v)}%'),
            vol_cb(int(v)),
        ))

    def set_playing(self, p):
        self._btn_play.text = 'II' if p else ' >'

    def update(self, pos, dur):
        if dur > 0:
            self._seek.set_progress(pos / dur)
        self._lbl_pos.text = format_time(pos)
        self._lbl_dur.text = format_time(dur)

    def flash(self, txt):
        self._skip_lbl.text    = txt
        self._skip_lbl.opacity = 1
        Animation(opacity=0, duration=0.9).start(self._skip_lbl)


# ── Reproductor de video principal ────────────────────────────────────────────
class VideoPlayerScreen(FloatLayout):
    """
    Reproductor fullscreen estilo Netflix/YouTube.
    Usa kivy.uix.video.Video con ffpyplayer backend.
    state='play'/'pause'/'stop' — API moderna de Kivy 2.3.
    """

    def __init__(self, file_path, title='',
                 on_close=None, on_prev=None, on_next=None, **kw):
        super().__init__(**kw)
        self._file     = file_path
        self._on_close = on_close
        self._on_prev  = on_prev
        self._on_next  = on_next
        self._dur      = 0.0
        self._playing  = False
        self._vis      = True
        self._htimer   = None
        self._vol      = 80
        self._last_tap = 0.0
        self._tick_ev  = None

        # Fondo negro total
        with self.canvas.before:
            Color(0, 0, 0, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, 'pos', self.pos),
                  size=lambda *_: setattr(self._bg, 'size', self.size))

        self._build()
        # Iniciar reproducción tras un frame completo de renderizado
        Clock.schedule_once(self._load_and_play, 0.5)

    def _build(self):
        # ── Widget de video ───────────────────────────────────────────────────
        # Importar aquí para que os.environ ya esté configurado
        from kivy.uix.video import Video
        self._vid = Video(
            source='',          # source se asigna después en _load_and_play
            state='stop',
            fit_mode='contain',
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
        )
        self._vid.bind(
            duration=self._on_dur,
            eos=self._on_eos,
        )
        self.add_widget(self._vid)

        # ── Controles overlay ─────────────────────────────────────────────────
        self._ctrl = _YTControls(
            title=self._file.replace('\\', '/').split('/')[-1],
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
        )
        self._ctrl.wire(
            play_cb  = self._toggle,
            prev_cb  = self._prev,
            next_cb  = self._next,
            rew_cb   = self._rew,
            ff_cb    = self._ff,
            seek_cb  = self._seek,
            vol_cb   = self._set_vol,
            close_cb = self._close,
        )
        self.add_widget(self._ctrl)
        self.bind(on_touch_down=self._tap)
        # PC: mouse move reactiva los controles
        try:
            from kivy.core.window import Window as _W
            _W.bind(mouse_pos=self._on_mouse_move)
        except Exception:
            pass

    def _load_and_play(self, dt):
        """Asignar source y reproducir con backend listo."""
        try:
            # Normalizar path (barras diagonales)
            self._vid.source = self._file.replace('\\', '/')
            # Pequeño delay más para que el source se aplique
            Clock.schedule_once(self._start_play, 0.3)
        except Exception as e:
            print(f'[Video] Error al cargar: {e}')

    def _start_play(self, dt):
        try:
            self._vid.state = 'play'
            self._playing   = True
            self._ctrl.set_playing(True)
            self._sched_hide()
            self._tick_ev = Clock.schedule_interval(self._tick, 0.4)
        except Exception as e:
            print(f'[Video] Error al reproducir: {e}')

    # ── Tick de actualización ─────────────────────────────────────────────────
    def _tick(self, dt):
        if not self._vid:
            return
        try:
            pos = self._vid.position or 0
            dur = self._vid.duration or self._dur
            if dur > 0:
                self._ctrl.update(pos, dur)
                self._dur = dur
        except Exception:
            pass

    def _on_dur(self, instance, value):
        if value and value > 0:
            self._dur = value

    def _on_eos(self, *_):
        self._playing = False
        self._ctrl.set_playing(False)
        if self._on_next:
            self._on_next()

    # ── Controles ─────────────────────────────────────────────────────────────
    def _toggle(self):
        try:
            if self._vid.state == 'play':
                self._vid.state  = 'pause'
                self._playing    = False
                self._ctrl.set_playing(False)
                self._cancel_hide()
                self._show()
            else:
                self._vid.state  = 'play'
                self._playing    = True
                self._ctrl.set_playing(True)
                self._sched_hide()
        except Exception as e:
            print(f'[Video] Toggle error: {e}')

    def _prev(self):
        self._stop_all()
        if self._on_prev:
            self._on_prev()

    def _next(self):
        self._stop_all()
        if self._on_next:
            self._on_next()

    def _rew(self):
        if self._dur > 0:
            try:
                pos = self._vid.position or 0
                self._vid.seek(max(0, pos - 10) / self._dur)
                self._ctrl.flash('-10s')
            except Exception:
                pass

    def _ff(self):
        if self._dur > 0:
            try:
                pos = self._vid.position or 0
                self._vid.seek(min(self._dur, pos + 10) / self._dur)
                self._ctrl.flash('+10s')
            except Exception:
                pass

    def _seek(self, v):
        try:
            self._vid.seek(v)
        except Exception:
            pass

    def _set_vol(self, v):
        self._vol = v
        try:
            self._vid.volume = v / 100
        except Exception:
            pass

    def _close(self):
        # Desconectar listener de mouse al cerrar
        try:
            from kivy.core.window import Window
            Window.unbind(mouse_pos=self._on_mouse_move)
        except Exception:
            pass
        self._stop_all()
        if self._on_close:
            self._on_close()

    def _stop_all(self):
        if self._tick_ev:
            self._tick_ev.cancel()
            self._tick_ev = None
        self._cancel_hide()
        try:
            self._vid.state = 'stop'
            self._vid.unload()
        except Exception:
            pass

    # ── Visibilidad de controles ───────────────────────────────────────────────
    def _on_mouse_move(self, window, pos):
        """PC: cualquier movimiento del mouse muestra los controles."""
        if not self._vis:
            self._show()

    def _tap(self, _, touch):
        """Toque en la pantalla — toggle controles o doble-tap para skip."""
        # Si el toque es dentro de los controles, dejar que ellos lo manejen
        if self._ctrl.collide_point(*touch.pos):
            # Reiniciar el timer de auto-ocultar
            if self._playing:
                self._sched_hide()
            return False

        now = _time.time()
        if now - self._last_tap < 0.32:
            # Doble tap: skip
            if touch.x < self.center_x:
                self._rew()
            else:
                self._ff()
            self._last_tap = 0.0
        else:
            # Tap simple: mostrar/ocultar controles
            self._last_tap = now
            if self._vis:
                self._hide()
            else:
                self._show()
        return False

    def _show(self):
        """Mostrar controles y programar auto-ocultado si está reproduciendo."""
        self._vis = True
        Animation.cancel_all(self._ctrl, 'opacity')
        self._ctrl.opacity = 1
        if self._playing:
            self._sched_hide()

    def _hide(self):
        """Ocultar controles suavemente (solo si está reproduciendo)."""
        if self._playing:
            self._vis = False
            Animation.cancel_all(self._ctrl, 'opacity')
            Animation(opacity=0, duration=0.4).start(self._ctrl)

    def _sched_hide(self):
        self._cancel_hide()
        self._htimer = Clock.schedule_once(lambda dt: self._hide(), 4.0)

    def _cancel_hide(self):
        if self._htimer:
            self._htimer.cancel()
            self._htimer = None
