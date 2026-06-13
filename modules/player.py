"""
Motor de reproducción de audio y video
Usa android.media en Android, vlc en escritorio (fallback a pygame/kivy)
"""
import threading
import time
from kivy.utils import platform
from kivy.clock import Clock


class AudioPlayer:
    """Reproductor de audio multiplataforma"""

    def __init__(self):
        self._backend = None
        self._position = 0.0
        self._duration = 0.0
        self._playing = False
        self._volume = 70
        self._current_file = None
        self._update_event = None
        self.on_end_callback = None
        self.on_position_callback = None
        self._init_backend()

    # ── Backend ───────────────────────────────────────────────────────────────
    def _init_backend(self):
        if platform == 'android':
            self._backend = _AndroidAudio()
        else:
            # Intentar VLC primero
            try:
                import vlc as _vlc  # noqa: F401
                self._backend = _VLCAudio()
            except ImportError:
                # Fallback a Kivy SoundLoader
                self._backend = _KivyAudio()

        if self._backend:
            self._backend.on_end = self._on_end
            self._backend.on_position = self._on_position_update

    # ── API pública ───────────────────────────────────────────────────────────
    def load(self, file_path: str):
        self._current_file = file_path
        if self._backend:
            self._backend.load(file_path)
            self._duration = self._backend.get_duration()
        self._position = 0.0

    def play(self):
        if self._backend:
            self._backend.play()
            self._playing = True

    def pause(self):
        if self._backend:
            self._backend.pause()
            self._playing = False

    def stop(self):
        if self._backend:
            self._backend.stop()
        self._playing = False
        self._position = 0.0

    def seek(self, position: float):
        """position en segundos"""
        if self._backend:
            self._backend.seek(position)
        self._position = position

    def set_volume(self, volume: int):
        """volume 0-100"""
        self._volume = max(0, min(100, volume))
        if self._backend:
            self._backend.set_volume(self._volume)

    def get_position(self) -> float:
        if self._backend:
            return self._backend.get_position()
        return self._position

    def get_duration(self) -> float:
        if self._backend:
            return self._backend.get_duration()
        return self._duration

    def is_playing(self) -> bool:
        if self._backend:
            return self._backend.is_playing()
        return self._playing

    # ── Callbacks ─────────────────────────────────────────────────────────────
    def _on_end(self):
        self._playing = False
        if self.on_end_callback:
            Clock.schedule_once(lambda dt: self.on_end_callback(), 0)

    def _on_position_update(self, pos):
        self._position = pos
        if self.on_position_callback:
            self.on_position_callback(pos)


# ══════════════════════════════════════════════════════════════════════════════
# Backends concretos
# ══════════════════════════════════════════════════════════════════════════════

class _VLCAudio:
    def __init__(self):
        import vlc
        self._vlc = vlc
        # Suprimir logs verbosos de VLC (stale plugins cache, COM errors)
        # '--reset-plugins-cache' regenera el caché y elimina los warnings
        self._instance = vlc.Instance(
            '--no-xlib',
            '--quiet',
            '--reset-plugins-cache',
            '--aout=directsound',   # Windows: evita el error COM de mmdevice
        )
        self._player = self._instance.media_player_new()
        self.on_end = None
        self.on_position = None
        self._duration = 0.0
        self._event = None
        self._setup_events()
        # Hilo de posición
        self._running = True
        self._thread = threading.Thread(target=self._pos_thread, daemon=True)
        self._thread.start()

    def _setup_events(self):
        mgr = self._player.event_manager()
        mgr.event_attach(
            self._vlc.EventType.MediaPlayerEndReached,
            lambda e: self.on_end() if self.on_end else None
        )

    def _pos_thread(self):
        while self._running:
            time.sleep(0.5)
            if self.on_position and self._player.is_playing():
                pos = self._player.get_time() / 1000
                self.on_position(pos)

    def load(self, path):
        media = self._instance.media_new(path)
        self._player.set_media(media)
        # Pre-parse para obtener duración
        self._player.play()
        time.sleep(0.3)
        self._player.pause()
        self._player.set_time(0)
        self._duration = self._player.get_length() / 1000

    def play(self):
        self._player.play()

    def pause(self):
        self._player.pause()

    def stop(self):
        self._player.stop()

    def seek(self, pos):
        self._player.set_time(int(pos * 1000))

    def set_volume(self, vol):
        self._player.audio_set_volume(int(vol))

    def get_position(self):
        return max(0, self._player.get_time() / 1000)

    def get_duration(self):
        d = self._player.get_length() / 1000
        return d if d > 0 else self._duration

    def is_playing(self):
        return self._player.is_playing() == 1


class _KivyAudio:
    """Fallback usando Kivy SoundLoader"""
    def __init__(self):
        self._sound = None
        self._duration = 0.0
        self._start_time = 0.0
        self._paused_pos = 0.0
        self._playing = False
        self.on_end = None
        self.on_position = None
        self._event = None

    def load(self, path):
        from kivy.core.audio import SoundLoader
        if self._sound:
            self._sound.stop()
            self._sound.unload()
        self._sound = SoundLoader.load(path)
        if self._sound:
            self._sound.bind(on_stop=self._on_stop)
            self._duration = self._sound.length or 0.0
        self._paused_pos = 0.0

    def play(self):
        if self._sound:
            self._sound.seek(self._paused_pos)
            self._sound.play()
            self._playing = True
            self._start_time = time.time() - self._paused_pos
            self._event = Clock.schedule_interval(self._tick, 0.5)

    def pause(self):
        if self._sound:
            self._paused_pos = self.get_position()
            self._sound.stop()
            self._playing = False
            if self._event:
                self._event.cancel()

    def stop(self):
        if self._sound:
            self._sound.stop()
        self._playing = False
        self._paused_pos = 0.0
        if self._event:
            self._event.cancel()

    def seek(self, pos):
        self._paused_pos = pos
        if self._playing and self._sound:
            self._sound.seek(pos)

    def set_volume(self, vol):
        if self._sound:
            self._sound.volume = vol / 100

    def get_position(self):
        if self._playing:
            return time.time() - self._start_time
        return self._paused_pos

    def get_duration(self):
        return self._duration

    def is_playing(self):
        return self._playing

    def _tick(self, dt):
        if self.on_position and self._playing:
            self.on_position(self.get_position())

    def _on_stop(self, *args):
        self._playing = False
        if self._event:
            self._event.cancel()
        if self.on_end:
            self.on_end()


class _AndroidAudio:
    """Backend nativo Android usando android.media.MediaPlayer vía pyjnius"""
    def __init__(self):
        self._player = None
        self._duration = 0.0
        self._playing = False
        self.on_end = None
        self.on_position = None
        self._event = None
        try:
            from jnius import autoclass  # type: ignore
            self._MediaPlayer = autoclass('android.media.MediaPlayer')
            self._player = self._MediaPlayer()
        except Exception as e:
            print(f'[AndroidAudio] No se pudo iniciar MediaPlayer: {e}')
            self._player = None

    def load(self, path):
        if not self._player:
            return
        try:
            self._player.reset()
            self._player.setDataSource(path)
            self._player.prepare()
            self._duration = self._player.getDuration() / 1000
            self._player.setOnCompletionListener(self._make_completion_listener())
        except Exception as e:
            print(f'[AndroidAudio] Error cargando: {e}')

    def play(self):
        if self._player:
            self._player.start()
            self._playing = True
            self._event = Clock.schedule_interval(self._tick, 0.5)

    def pause(self):
        if self._player:
            self._player.pause()
            self._playing = False
            if self._event:
                self._event.cancel()

    def stop(self):
        if self._player:
            self._player.stop()
        self._playing = False
        if self._event:
            self._event.cancel()

    def seek(self, pos):
        if self._player:
            self._player.seekTo(int(pos * 1000))

    def set_volume(self, vol):
        if self._player:
            v = vol / 100
            self._player.setVolume(v, v)

    def get_position(self):
        if self._player:
            try:
                return self._player.getCurrentPosition() / 1000
            except Exception:
                pass
        return 0.0

    def get_duration(self):
        return self._duration

    def is_playing(self):
        if self._player:
            try:
                return self._player.isPlaying()
            except Exception:
                pass
        return False

    def _tick(self, dt):
        if self.on_position and self.is_playing():
            self.on_position(self.get_position())

    def _make_completion_listener(self):
        on_end = self.on_end
        try:
            from jnius import PythonJavaClass, java_method  # type: ignore
            class Listener(PythonJavaClass):
                __javainterfaces__ = ['android/media/MediaPlayer$OnCompletionListener']
                @java_method('(Landroid/media/MediaPlayer;)V')
                def onCompletion(self, mp):
                    if on_end:
                        Clock.schedule_once(lambda dt: on_end(), 0)
            return Listener()
        except Exception:
            return None
