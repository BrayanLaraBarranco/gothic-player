"""
Reproductor de Audio — Gothic Player Pro
- Portada grande arriba (como imagen 2 de referencia)
- Título + artista centrados debajo de la portada
- Seekbar + controles compactos abajo
- Transparencia alta para ver la imagen de fondo
"""
import os
from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.floatlayout  import FloatLayout
from kivy.uix.label        import Label
from kivy.uix.button       import Button
from kivy.uix.slider       import Slider
from kivy.uix.image        import Image as KivyImage
from kivy.graphics         import (Color, Rectangle, RoundedRectangle,
                                    Line, Ellipse)
from kivy.clock            import Clock
from kivy.metrics          import dp, sp
from kivy.properties       import (StringProperty, NumericProperty,
                                    BooleanProperty, ObjectProperty)
from kivy.animation        import Animation

from ui.theme      import theme, SeekBar
from modules.utils import format_time


class _CBtn(Button):
    def __init__(self, txt, cb=None, big=False, **kw):
        super().__init__(text=txt, **kw)
        self._big              = big
        sz                     = dp(54) if big else dp(38)
        self.size_hint         = (None, None)
        self.size              = (sz, sz)
        self.background_normal = ''
        self.background_down   = ''
        self.background_color  = (0, 0, 0, 0)
        self.color             = list(theme.gold)
        self.font_size         = sp(16) if big else sp(11)
        self.bold              = True
        with self.canvas.before:
            if big:
                self._c_r2 = Color(*theme.gold_muted)
                self._e_r2 = Ellipse(pos=self.pos, size=self.size)
            else:
                self._c_r2 = None; self._e_r2 = None
            self._c_r1 = Color(*theme.gold_dark)
            p1 = dp(3) if big else dp(2)
            self._e_r1 = Ellipse(pos=(self.x+p1,self.y+p1),
                                  size=(self.width-p1*2,self.height-p1*2))
            fill = list(theme.accent) if big else (*theme.surface[:3], 0.55)
            self._c_f  = Color(*fill)
            p2 = dp(6) if big else dp(4)
            self._e_f  = Ellipse(pos=(self.x+p2,self.y+p2),
                                  size=(self.width-p2*2,self.height-p2*2))
        self.bind(pos=self._upd, size=self._upd, state=self._st)
        theme.register_widget(self)
        if cb: self.bind(on_release=lambda *_: cb())

    def _upd(self, *_):
        p1 = dp(3) if self._big else dp(2)
        p2 = dp(6) if self._big else dp(4)
        if self._e_r2:
            self._e_r2.pos=self.pos; self._e_r2.size=self.size
        self._e_r1.pos=(self.x+p1,self.y+p1); self._e_r1.size=(self.width-p1*2,self.height-p1*2)
        self._e_f.pos=(self.x+p2,self.y+p2);  self._e_f.size=(self.width-p2*2,self.height-p2*2)

    def _st(self, *_):
        self._c_f.rgba = (list(theme.accent_hover) if self.state=='down'
                          else (list(theme.accent) if self._big
                                else [*theme.surface[:3], 0.55]))

    def set_active(self, v):
        self._c_f.rgba = (list(theme.accent_hover) if v
                          else (list(theme.accent) if self._big
                                else [*theme.surface[:3], 0.55]))

    def on_theme_update(self):
        if self._c_r2: self._c_r2.rgba = list(theme.gold_muted)
        self._c_r1.rgba = list(theme.gold_dark)
        self._c_f.rgba  = (list(theme.accent) if self._big
                           else [*theme.surface[:3], 0.55])
        self.color = list(theme.gold)


class _VolSlider(Slider):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.cursor_image = ''
        self.cursor_size  = (1, 1)
        self.bind(pos=self._rd, size=self._rd, value=self._rd)
        theme.register_widget(self)

    def on_theme_update(self): self._rd()

    def _rd(self, *_):
        self.canvas.after.clear()
        with self.canvas.after:
            y=self.center_y; x0=self.x+dp(4); tw=self.width-dp(8); h=dp(4)
            Color(*theme.get('seekbar_bg'))
            RoundedRectangle(pos=(x0,y-h/2), size=(tw,h), radius=[h/2])
            r=((self.value-self.min)/(self.max-self.min)
               if self.max>self.min else 0)
            if r>0:
                Color(*theme.accent)
                RoundedRectangle(pos=(x0,y-h/2), size=(tw*r,h), radius=[h/2])
            tx=x0+tw*r; tr=dp(8)
            Color(*theme.gold)
            Ellipse(pos=(tx-tr,y-tr), size=(tr*2,tr*2))
            Color(*theme.gold_dark)
            Line(circle=(tx,y,tr-1), width=1.2)


class AudioPlayerWidget(BoxLayout):
    current_song   = StringProperty('')
    current_title  = StringProperty('-- Silence --')
    current_artist = StringProperty('Unknown Artist')
    is_playing     = BooleanProperty(False)
    repeat_mode    = NumericProperty(0)
    shuffle_on     = BooleanProperty(False)
    volume         = NumericProperty(70)
    playlist_callback = ObjectProperty(None, allownone=True)
    status_callback   = ObjectProperty(None, allownone=True)

    def __init__(self, audio_player, library, **kw):
        super().__init__(**kw)
        self.orientation = 'vertical'
        self._player   = audio_player
        self._library  = library
        self._timer    = None
        self._duration = 0.0

        with self.canvas.before:
            self._c_bg = Color(*theme.bg2[:3], 0.35)
            self._r_bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd_bg, size=self._upd_bg)
        self._player.on_end_callback      = self._on_end
        self._player.on_position_callback = lambda p: None
        self._build()
        theme.register_widget(self)

    def _upd_bg(self, *_):
        self._r_bg.pos=self.pos; self._r_bg.size=self.size

    def on_theme_update(self):
        self._c_bg.rgba    = (*theme.bg2[:3], 0.35)
        self._c_bot.rgba   = (*theme.bg2[:3], 0.50)
        self._c_bot_l.rgba = list(theme.gold_dark)
        self._lbl_title.color  = (1.0, 0.96, 0.88, 1.0)
        self._lbl_artist.color = list(theme.gold_muted)
        self._lbl_pos.color    = list(theme.gold_muted)
        self._lbl_dur.color    = list(theme.gold_muted)
        self._lbl_vol.color    = list(theme.gold)
        self._c_cover_bd.rgba  = list(theme.gold_dark)

    def _build(self):
        # ── Portada GRANDE — ocupa la mayor parte del panel ───────────────
        cover_wrap = FloatLayout(size_hint=(1, 1))  # crece con el panel

        self._cover_img = KivyImage(
            source='', fit_mode='cover',
            size_hint=(None, None),
            pos_hint={'center_x': 0.5, 'center_y': 0.5})

        # Borde dorado ornamental
        with self._cover_img.canvas.after:
            self._c_cover_bd = Color(*theme.gold_dark)
            self._r_cover_bd = Line(
                rounded_rectangle=(self._cover_img.x, self._cover_img.y,
                                   self._cover_img.width, self._cover_img.height,
                                   dp(4)), width=2.0)

        def _upd_cover(*_):
            # Portada cuadrada que ocupa el ancho disponible menos padding
            sz = min(self._cover_img.parent.width if self._cover_img.parent
                     else dp(300), dp(320)) - dp(24)
            self._cover_img.size = (sz, sz)
            self._r_cover_bd.rounded_rectangle = (
                self._cover_img.x, self._cover_img.y,
                self._cover_img.width, self._cover_img.height, dp(4))

        self._cover_img.bind(pos=_upd_cover, size=_upd_cover)
        cover_wrap.bind(size=lambda w, s: Clock.schedule_once(
            lambda dt: _upd_cover(), 0))
        cover_wrap.add_widget(self._cover_img)
        self.add_widget(cover_wrap)

        # ── Info: título + artista ────────────────────────────────────────
        info = BoxLayout(orientation='vertical', size_hint_y=None,
                         height=dp(54), padding=[dp(12), dp(4)], spacing=dp(2))

        self._lbl_title = Label(
            text=self.current_title,
            color=(1.0, 0.96, 0.88, 1.0),
            font_size=sp(16), bold=True, halign='center',
            size_hint_y=None, height=dp(28),
            shorten=True, shorten_from='right')
        self._lbl_title.bind(
            size=lambda w,s: setattr(w,'text_size',(s[0],None)))

        self._lbl_artist = Label(
            text=f'– {self.current_artist} –',
            color=list(theme.gold_muted),
            font_size=sp(11), italic=True, halign='center',
            size_hint_y=None, height=dp(18),
            shorten=True, shorten_from='right')
        self._lbl_artist.bind(
            size=lambda w,s: setattr(w,'text_size',(s[0],None)))

        info.add_widget(self._lbl_title)
        info.add_widget(self._lbl_artist)
        self.add_widget(info)

        # ── Zona de controles ─────────────────────────────────────────────
        bottom = BoxLayout(orientation='vertical',
                           size_hint_y=None, height=dp(148),
                           padding=[dp(10), dp(4), dp(10), dp(8)],
                           spacing=dp(3))
        with bottom.canvas.before:
            self._c_bot   = Color(*theme.bg2[:3], 0.50)
            self._r_bot   = Rectangle(pos=bottom.pos, size=bottom.size)
            self._c_bot_l = Color(*theme.gold_dark)
            self._r_bot_l = Line(
                points=[bottom.x,bottom.top,bottom.right,bottom.top], width=1.2)
        bottom.bind(pos=self._upd_bot, size=self._upd_bot)

        # Seekbar
        sw = BoxLayout(orientation='vertical', size_hint_y=None,
                       height=dp(30), spacing=dp(1))
        self._seek = SeekBar()
        self._seek.on_seek = self._on_seek
        sw.add_widget(self._seek)
        tr = BoxLayout(size_hint_y=None, height=dp(12))
        self._lbl_pos = Label(text='0:00', color=list(theme.gold_muted),
                              font_size=sp(8), halign='left')
        self._lbl_pos.bind(size=lambda w,s: setattr(w,'text_size',s))
        self._lbl_dur = Label(text='0:00', color=list(theme.gold_muted),
                              font_size=sp(8), halign='right')
        self._lbl_dur.bind(size=lambda w,s: setattr(w,'text_size',s))
        tr.add_widget(self._lbl_pos); tr.add_widget(self._lbl_dur)
        sw.add_widget(tr)
        bottom.add_widget(sw)

        # Fila principal — X | prev | PLAY | next | R
        c1 = BoxLayout(size_hint_y=None, height=dp(58),
                       spacing=dp(6), padding=[0, dp(2)])
        self._b_shuf = _CBtn('X',  self._toggle_shuf)
        self._b_prev = _CBtn('|<', self._prev)
        self._b_play = _CBtn(' >', self._toggle, big=True)
        self._b_next = _CBtn('>|', self._next)
        self._b_rep  = _CBtn('R',  self._toggle_rep)
        for b in (self._b_shuf,self._b_prev,self._b_play,
                  self._b_next,self._b_rep):
            c1.add_widget(b)
        bottom.add_widget(c1)

        # Fila secundaria — A-B | # | << | >> | ■
        c2 = BoxLayout(size_hint_y=None, height=dp(32), spacing=dp(4))
        for txt,cb in [('A-B',None),('#',None),('<<',self._rew),
                       ('>>',self._ff),('■',self._stop)]:
            c2.add_widget(_CBtn(txt, cb))
        bottom.add_widget(c2)

        # Volumen
        vr = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(4))
        bm = _CBtn('-', self._vol_down); bm.size=(dp(26),dp(26))
        vr.add_widget(bm)
        self._vol_sl = _VolSlider(min=0, max=100, value=self.volume)
        self._vol_sl.bind(value=self._on_vol)
        vr.add_widget(self._vol_sl)
        bp = _CBtn('+', self._vol_up); bp.size=(dp(26),dp(26))
        vr.add_widget(bp)
        self._lbl_vol = Label(text=f'{int(self.volume)}%',
                              color=list(theme.gold), font_size=sp(11), bold=True,
                              size_hint=(None,1), width=dp(38), halign='center')
        vr.add_widget(self._lbl_vol)
        bottom.add_widget(vr)
        self.add_widget(bottom)

    def _upd_bot(self, w, *_):
        self._r_bot.pos=w.pos; self._r_bot.size=w.size
        self._r_bot_l.points=[w.x,w.top,w.right,w.top]

    # ── API ────────────────────────────────────────────────────────────────
    def play_song(self, fp, meta):
        self.current_song   = fp
        self.current_title  = meta.get('title',  'Sin título')
        self.current_artist = meta.get('artist', 'Desconocido')
        self._lbl_title.text  = self.current_title
        self._lbl_artist.text = f'– {self.current_artist} –'
        cover = self._library.get_cover_path(fp)
        self._cover_img.source = cover or ''
        if cover: self._cover_img.reload()
        self._player.load(fp)
        self._player.set_volume(int(self.volume))
        self._player.play()
        self.is_playing = True
        self._b_play.text = 'II'
        self._duration = 0.0
        Clock.schedule_once(lambda dt: self._fetch_dur(), 0.6)
        if self.status_callback:
            self.status_callback(self.current_title, self.current_artist)
        if self._timer: self._timer.cancel()
        self._timer = Clock.schedule_interval(self._tick, 0.5)

    def set_playlist_callback(self, cb): self.playlist_callback = cb

    def _toggle(self):
        if self.is_playing:
            self._player.pause(); self.is_playing=False; self._b_play.text=' >'
        else:
            self._player.play();  self.is_playing=True;  self._b_play.text='II'

    def _stop(self):
        self._player.stop(); self.is_playing=False
        self._b_play.text=' >'; self._seek.progress=0.0; self._lbl_pos.text='0:00'

    def _prev(self):
        if self.playlist_callback: self.playlist_callback('prev')
    def _next(self):
        if self.playlist_callback: self.playlist_callback('next')
    def _rew(self):
        self._player.seek(max(0, self._player.get_position()-10))
    def _ff(self):
        if self._duration>0:
            self._player.seek(min(self._duration, self._player.get_position()+10))
    def _toggle_shuf(self):
        self.shuffle_on=not self.shuffle_on; self._b_shuf.set_active(self.shuffle_on)
    def _toggle_rep(self):
        self.repeat_mode=(self.repeat_mode+1)%3
        self._b_rep.text=['R','R1','R+'][self.repeat_mode]
        self._b_rep.set_active(self.repeat_mode>0)
    def _vol_down(self): self._vol_sl.value=max(0,self._vol_sl.value-5)
    def _vol_up(self):   self._vol_sl.value=min(100,self._vol_sl.value+5)
    def _on_vol(self,_,v):
        self.volume=v; self._lbl_vol.text=f'{int(v)}%'
        self._player.set_volume(int(v))
    def _on_seek(self, val):
        if self._duration>0: self._player.seek(val*self._duration)
    def _fetch_dur(self):
        self._duration=self._player.get_duration()
        self._lbl_dur.text=format_time(self._duration)
    def _tick(self, dt):
        if self._duration>0 and not self._seek._dragging:
            pos=self._player.get_position()
            self._seek.progress=min(1.0, pos/self._duration)
            self._lbl_pos.text=format_time(pos)
        elif self._duration==0:
            d=self._player.get_duration()
            if d>0: self._duration=d; self._lbl_dur.text=format_time(d)
    def _on_end(self):
        if self.repeat_mode==2:
            self._player.seek(0); self._player.play()
        elif self.playlist_callback:
            self.playlist_callback('next_loop' if self.repeat_mode==1 else 'next')
        else:
            self.is_playing=False; self._b_play.text=' >'
