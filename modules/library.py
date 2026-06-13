"""
Gestión de biblioteca de medios — Gothic Player Pro
Extracción robusta de metadatos y miniaturas para MP3, MP4, FLAC, WAV, MKV.
"""
import json
import subprocess
from pathlib import Path
from config import PLAYLIST_FILE, AUDIO_EXTENSIONS, VIDEO_EXTENSIONS, COVERS_FOLDER


class Library:

    def __init__(self):
        self.playlist: list       = []
        self.metadata_cache: dict = {}
        self.load()

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def add(self, file_path: str) -> bool:
        fp = str(Path(file_path).resolve())
        if fp not in self.playlist and Path(fp).exists():
            self.playlist.append(fp)
            self.save()
            self._extract_cover(fp)
            self._load_metadata(fp)
            return True
        return False

    def remove(self, file_path: str) -> bool:
        if file_path in self.playlist:
            self.playlist.remove(file_path)
            self.metadata_cache.pop(file_path, None)
            self.save()
            return True
        return False

    # ── Consultas ─────────────────────────────────────────────────────────────
    def get_all(self) -> list:
        return self.playlist.copy()

    def get_audio_files(self) -> list:
        return [f for f in self.playlist
                if Path(f).suffix.lower() in AUDIO_EXTENSIONS]

    def get_video_files(self) -> list:
        return [f for f in self.playlist
                if Path(f).suffix.lower() in VIDEO_EXTENSIONS]

    def get_metadata(self, file_path: str) -> dict:
        if file_path in self.metadata_cache:
            return self.metadata_cache[file_path]

        info = self._build_metadata(file_path)
        self.metadata_cache[file_path] = info
        return info

    def _build_metadata(self, file_path: str) -> dict:
        """Extrae metadatos completos de cualquier formato."""
        p    = Path(file_path)
        stem = p.stem
        ext  = p.suffix.lower()

        info = {
            'title':     stem,
            'artist':    'Desconocido',
            'album':     'Sin álbum',
            'channel':   '',
            'year':      '',
            'genre':     '',
            'duration':  0,
            'thumbnail': '',
        }

        # ── 1. Sidecar JSON de yt-dlp (máxima prioridad) ─────────────────────
        for json_path in (p.with_suffix('.json'),
                          p.parent / f'{stem}.info.json'):
            if json_path.exists():
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        j = json.load(f)
                    info['title']    = j.get('title',    info['title'])
                    info['artist']   = (j.get('artist') or j.get('uploader') or
                                        j.get('channel') or info['artist'])
                    info['album']    = (j.get('album') or j.get('playlist') or
                                        info['album'])
                    info['channel']  = j.get('channel') or j.get('uploader', '')
                    info['year']     = str(j.get('upload_date', '')[:4]).strip('0') or \
                                       str(j.get('release_year', ''))
                    info['genre']    = j.get('genre', '')
                    info['duration'] = j.get('duration', 0) or 0
                    info['thumbnail']= j.get('thumbnail', '')
                    break
                except Exception:
                    pass

        # ── 2. Tags embebidos (mutagen) ───────────────────────────────────────
        try:
            from mutagen import File as MutagenFile
            mf = MutagenFile(file_path, easy=True)
            if mf:
                info['duration'] = info['duration'] or \
                                   getattr(mf.info, 'length', 0) or 0
                tags = mf.tags or {}
                def _t(key):
                    v = tags.get(key)
                    return str(v[0]) if v else ''

                if ext in ('.mp3', '.flac', '.ogg', '.m4a', '.aac'):
                    info['title']  = info['title']  or _t('title')  or stem
                    info['artist'] = info['artist'] if info['artist'] != 'Desconocido' \
                                     else (_t('artist') or 'Desconocido')
                    info['album']  = info['album']  if info['album']  != 'Sin álbum' \
                                     else (_t('album')  or 'Sin álbum')
                    info['year']   = info['year']   or _t('date') or _t('year')
                    info['genre']  = info['genre']  or _t('genre')
        except Exception:
            pass

        # ── 3. ffprobe para duración de video ─────────────────────────────────
        if ext in VIDEO_EXTENSIONS and info['duration'] == 0:
            try:
                r = subprocess.run(
                    ['ffprobe', '-v', 'quiet', '-print_format', 'json',
                     '-show_format', file_path],
                    capture_output=True, text=True, timeout=8)
                d = json.loads(r.stdout)
                info['duration'] = float(
                    d.get('format', {}).get('duration', 0))
                # También tags de ffprobe
                tags = d.get('format', {}).get('tags', {})
                if tags:
                    info['title']  = info['title']  or tags.get('title', stem)
                    info['artist'] = (info['artist'] if info['artist'] != 'Desconocido'
                                      else tags.get('artist', tags.get('ARTIST', 'Desconocido')))
                    info['album']  = (info['album'] if info['album'] != 'Sin álbum'
                                      else tags.get('album', 'Sin álbum'))
            except Exception:
                pass

        info['title'] = info['title'] or stem
        return info

    def get_cover_path(self, file_path: str) -> str | None:
        """Devuelve ruta a miniatura existente o la extrae."""
        base  = Path(file_path).stem
        # Buscar miniatura ya extraída
        for ext in ('jpg', 'jpeg', 'png', 'webp'):
            cover = COVERS_FOLDER / f'{base}.{ext}'
            if cover.exists():
                return str(cover)
        # Intentar extraer
        result = self._extract_cover(file_path)
        if result and Path(result).exists():
            return result
        return None

    def search(self, query: str) -> list:
        q = query.lower()
        return [
            f for f in self.playlist
            if q in self.get_metadata(f)['title'].lower()
            or q in self.get_metadata(f)['artist'].lower()
            or q in Path(f).stem.lower()
        ]

    # ── Persistencia ──────────────────────────────────────────────────────────
    def save(self):
        try:
            PLAYLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(PLAYLIST_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.playlist, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f'[Library] Error guardando: {e}')

    def load(self):
        try:
            if PLAYLIST_FILE.exists():
                with open(PLAYLIST_FILE, 'r', encoding='utf-8') as f:
                    self.playlist = [p for p in json.load(f)
                                     if Path(p).exists()]
        except Exception:
            self.playlist = []

    def clear_cache(self):
        self.metadata_cache.clear()

    # ── Extracción de miniaturas ───────────────────────────────────────────────
    def _extract_cover(self, file_path: str) -> str | None:
        """
        Extrae miniatura de audio o video.
        Retorna la ruta de la imagen guardada o None.
        """
        p    = Path(file_path)
        stem = p.stem
        ext  = p.suffix.lower()
        COVERS_FOLDER.mkdir(parents=True, exist_ok=True)
        out  = COVERS_FOLDER / f'{stem}.jpg'

        if out.exists():
            return str(out)

        # ── A. Imagen ya existente junto al archivo (descargada por yt-dlp) ──
        for img_ext in ('jpg', 'jpeg', 'png', 'webp'):
            candidate = p.parent / f'{stem}.{img_ext}'
            if candidate.exists():
                try:
                    import shutil
                    shutil.copy2(str(candidate), str(out))
                    return str(out)
                except Exception:
                    pass

        # ── B. Tag APIC embebido (MP3 / FLAC / M4A) ──────────────────────────
        if ext in ('.mp3', '.flac', '.m4a', '.ogg', '.aac'):
            result = self._extract_cover_audio(file_path, out)
            if result:
                return result

        # ── C. Frame de video con ffmpeg ──────────────────────────────────────
        if ext in VIDEO_EXTENSIONS:
            result = self._extract_cover_video(file_path, out)
            if result:
                return result

        # ── D. Miniatura de thumbnail file (.jpg/.webp junto al video) ────────
        for img_ext in ('jpg', 'jpeg', 'png', 'webp'):
            # Nombre exacto con extensión diferente
            candidate = p.with_suffix(f'.{img_ext}')
            if candidate.exists():
                try:
                    import shutil
                    shutil.copy2(str(candidate), str(out))
                    return str(out)
                except Exception:
                    pass

        return None

    def _extract_cover_audio(self, file_path: str, out: Path) -> str | None:
        """Extrae APIC tag de archivos de audio con mutagen."""
        try:
            from mutagen import File as MutagenFile
            audio = MutagenFile(file_path)
            if audio is None or audio.tags is None:
                return None

            # ID3 (MP3)
            for key in audio.tags.keys():
                if key.startswith('APIC'):
                    data = audio.tags[key].data
                    if data:
                        with open(out, 'wb') as f:
                            f.write(data)
                        return str(out)

            # FLAC / Ogg (covr / metadata_block_picture)
            pics = audio.tags.get('covr') or \
                   audio.tags.get('METADATA_BLOCK_PICTURE') or \
                   audio.tags.get('metadata_block_picture')
            if pics:
                pic = pics[0]
                data = getattr(pic, 'data', pic)
                if data:
                    with open(out, 'wb') as f:
                        f.write(data if isinstance(data, bytes) else bytes(data))
                    return str(out)

        except Exception as e:
            print(f'[Library] cover audio {Path(file_path).name}: {e}')
        return None

    def _extract_cover_video(self, file_path: str, out: Path) -> str | None:
        """Extrae un frame del video con ffmpeg para usar como miniatura."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-y',
                 '-ss', '5',           # segundo 5 del video
                 '-i', file_path,
                 '-vframes', '1',
                 '-vf', 'scale=320:-1',
                 '-q:v', '3',
                 str(out)],
                capture_output=True,
                timeout=20
            )
            if result.returncode == 0 and out.exists():
                return str(out)
        except FileNotFoundError:
            # ffmpeg no instalado — intentar con segundo 0
            try:
                subprocess.run(
                    ['ffmpeg', '-y', '-i', file_path,
                     '-vframes', '1', str(out)],
                    capture_output=True, timeout=15)
                if out.exists():
                    return str(out)
            except Exception:
                pass
        except Exception as e:
            print(f'[Library] cover video {Path(file_path).name}: {e}')
        return None

    def _load_metadata(self, file_path: str):
        self.get_metadata(file_path)
