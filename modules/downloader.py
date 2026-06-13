"""
Módulo de descarga — yt-dlp
Descarga música/video con metadatos COMPLETOS y miniaturas automáticas.
Guarda sidecar JSON con todos los campos de yt-dlp para Library.
"""
import os
import json
import shutil
import threading
import subprocess
from pathlib import Path
from config import COVERS_FOLDER


class Downloader:
    def __init__(self, download_folder):
        self.download_folder = Path(download_folder)
        self.download_folder.mkdir(parents=True, exist_ok=True)
        self.is_downloading     = False
        self.current_progress   = 0.0
        self._progress_callback = None
        self._last_info         = {}   # guarda info de yt-dlp del último video

    def set_download_folder(self, folder):
        self.download_folder = Path(folder)
        self.download_folder.mkdir(parents=True, exist_ok=True)

    # ── API pública ───────────────────────────────────────────────────────────
    def download(self, url, format_type,
                 on_progress=None, on_complete=None, on_error=None):
        """Inicia descarga en hilo separado."""
        self._progress_callback = on_progress

        def _run():
            self.is_downloading   = True
            self.current_progress = 0.0
            try:
                import yt_dlp
                clean_url   = url.strip()
                is_playlist = 'list=' in clean_url and 'watch?v=' not in clean_url

                tmpl = str(self.download_folder / (
                    '%(playlist_index)s - %(title)s.%(ext)s'
                    if is_playlist else '%(title)s.%(ext)s'))

                ydl_opts = self._build_opts(format_type, tmpl, is_playlist)

                downloaded_entries = []

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(clean_url, download=True)

                if info is None:
                    if on_error:
                        on_error('No se pudo obtener información del video')
                    return

                entries = info.get('entries') if is_playlist else [info]

                for entry in (entries or []):
                    if not entry:
                        continue
                    result = self._process_entry(entry, format_type)
                    if result:
                        downloaded_entries.append(result)
                        if on_complete:
                            on_complete(result['path'],
                                        result['title'],
                                        result['artist'])
                    else:
                        title = entry.get('title', 'Desconocido')
                        if on_error:
                            on_error(f'No se encontró el archivo: {title}')

            except ImportError:
                if on_error:
                    on_error('yt-dlp no instalado. Ejecuta: pip install yt-dlp')
            except Exception as e:
                if on_error:
                    on_error(str(e)[:300])
            finally:
                self.is_downloading   = False
                self.current_progress = 0.0

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t

    def is_busy(self):
        return self.is_downloading

    def get_progress(self):
        return self.current_progress

    # ── Procesamiento de entrada ──────────────────────────────────────────────
    def _process_entry(self, entry: dict, format_type: str) -> dict | None:
        """
        Procesa una entrada de yt-dlp:
        - Encuentra el archivo descargado
        - Guarda JSON de metadatos completo
        - Extrae y guarda miniatura en COVERS_FOLDER
        Retorna dict con path, title, artist o None si falla.
        """
        title    = entry.get('title', 'Desconocido')
        artist   = (entry.get('artist') or entry.get('uploader') or
                    entry.get('channel') or 'Desconocido')
        album    = (entry.get('album') or entry.get('playlist_title') or
                    entry.get('playlist') or '')
        channel  = entry.get('channel') or entry.get('uploader', '')
        duration = entry.get('duration', 0) or 0
        year     = str(entry.get('upload_date', '') or '')[:4]
        year     = year if year.isdigit() else str(entry.get('release_year', '') or '')
        genre    = entry.get('genre', '') or entry.get('categories', [''])[0] \
                   if entry.get('categories') else ''
        thumbnail_url = entry.get('thumbnail', '')
        webpage_url   = entry.get('webpage_url', '')
        ext_real      = entry.get('ext', format_type)

        # Encontrar archivo en disco
        file_path = self._find_file(title, format_type, ext_real)
        if not file_path:
            return None

        stem = Path(file_path).stem

        # ── Miniatura ─────────────────────────────────────────────────────────
        cover_path = self._save_thumbnail(
            entry, stem, Path(file_path).parent)

        # ── Sidecar JSON completo ─────────────────────────────────────────────
        meta = {
            'title':         title,
            'artist':        artist,
            'album':         album,
            'channel':       channel,
            'year':          year,
            'genre':         genre,
            'duration':      duration,
            'thumbnail':     cover_path or thumbnail_url,
            'thumbnail_url': thumbnail_url,
            'webpage_url':   webpage_url,
            'format':        format_type,
            'view_count':    entry.get('view_count', 0),
            'like_count':    entry.get('like_count', 0),
            'description':   (entry.get('description', '') or '')[:500],
        }
        self._write_json(file_path, meta)

        return {
            'path':       file_path,
            'title':      title,
            'artist':     artist,
            'album':      album,
            'channel':    channel,
            'cover':      cover_path,
            'duration':   duration,
        }

    def _save_thumbnail(self, entry: dict, stem: str, folder: Path) -> str:
        """
        Guarda miniatura en COVERS_FOLDER.
        Orden de prioridad:
        1. Archivo de imagen ya descargado junto al audio/video
        2. URL de thumbnail de yt-dlp (descarga con requests)
        3. None
        """
        COVERS_FOLDER.mkdir(parents=True, exist_ok=True)
        out = COVERS_FOLDER / f'{stem}.jpg'

        if out.exists():
            return str(out)

        # ── 1. Buscar imagen junto al archivo descargado ──────────────────────
        for img_ext in ('jpg', 'jpeg', 'png', 'webp'):
            for pattern in (f'{stem}.{img_ext}', f'{stem}_thumb.{img_ext}'):
                candidate = folder / pattern
                if candidate.exists():
                    try:
                        shutil.copy2(str(candidate), str(out))
                        # Limpiar la imagen del directorio de descarga
                        try: candidate.unlink()
                        except Exception: pass
                        return str(out)
                    except Exception:
                        pass

        # ── 2. Descargar URL de thumbnail ────────────────────────────────────
        # Prefer max resolution thumbnail
        thumbnail_url = ''
        thumbnails = entry.get('thumbnails', [])
        if thumbnails:
            # Sort by resolution (width * height) descending
            def _res(t):
                return (t.get('width', 0) or 0) * (t.get('height', 0) or 0)
            best = max(thumbnails, key=_res, default=None)
            thumbnail_url = best.get('url', '') if best else ''
        if not thumbnail_url:
            thumbnail_url = entry.get('thumbnail', '')
        if thumbnail_url:
            try:
                import urllib.request
                req = urllib.request.Request(
                    thumbnail_url,
                    headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                with open(out, 'wb') as f:
                    f.write(data)
                # Convertir webp a jpg si es necesario
                self._ensure_jpg(out)
                return str(out)
            except Exception as e:
                print(f'[Downloader] Thumbnail download failed: {e}')

        return ''

    def _ensure_jpg(self, path: Path):
        """Convierte webp/png a jpg si PIL está disponible."""
        try:
            from PIL import Image
            img = Image.open(path).convert('RGB')
            img.save(str(path), 'JPEG', quality=90)
        except Exception:
            pass

    # ── Opciones yt-dlp ───────────────────────────────────────────────────────
    def _build_opts(self, format_type: str, tmpl: str, is_playlist: bool) -> dict:
        common = {
            'outtmpl':            tmpl,
            'quiet':              True,
            'no_warnings':        True,
            'ignoreerrors':       True,
            'yes_playlist':       is_playlist,
            'progress_hooks':     [self._progress_hook],
            # Guardar info JSON completo del video para metadatos
            'writeinfojson':      False,  # lo hacemos nosotros manualmente
            # Escribir miniatura al lado del archivo
            'writethumbnail':     True,
            'format_sort':        ['res:4320', 'br', 'vbr', 'abr'],
            'postprocessors': [{
                'key':            'FFmpegMetadata',
                'add_metadata':   True,
            }],
        }

        if format_type == 'mp3':
            return {
                **common,
                'format': 'bestaudio/best',
                'postprocessors': [
                    {'key': 'FFmpegExtractAudio',
                     'preferredcodec': 'mp3',
                     'preferredquality': '320'},
                    {'key': 'EmbedThumbnail'},      # embebe en MP3
                    {'key': 'FFmpegMetadata', 'add_metadata': True},
                ],
                'writethumbnail': True,
            }

        elif format_type == 'flac':
            return {
                **common,
                'format': 'bestaudio/best',
                'postprocessors': [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': 'flac'},
                    {'key': 'FFmpegMetadata', 'add_metadata': True},
                ],
            }

        elif format_type == 'wav':
            return {
                **common,
                'format': 'bestaudio/best',
                'postprocessors': [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav'},
                    {'key': 'FFmpegMetadata', 'add_metadata': True},
                ],
                'writethumbnail': True,
            }

        else:  # mp4 / mkv / avi / mov
            return {
                **common,
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best',
                'merge_output_format': format_type,
                'postprocessors': [
                    {'key': 'FFmpegMetadata', 'add_metadata': True},
                ],
                'writethumbnail': True,
            }

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _progress_hook(self, d):
        if d.get('status') == 'downloading':
            try:
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                done  = d.get('downloaded_bytes', 0)
                if total > 0:
                    self.current_progress = (done / total) * 100
                    if self._progress_callback:
                        self._progress_callback(self.current_progress)
            except Exception:
                pass

    def _find_file(self, title: str, fmt: str, ext_real: str = '') -> str | None:
        """
        Busca el archivo recién descargado.
        Prioridad: coincidencia de título > archivo más reciente.
        """
        # Extensiones a buscar
        exts = set()
        exts.add(f'.{fmt}')
        if ext_real:
            exts.add(f'.{ext_real}')
        # Audio puede quedar como .mp3 aunque fmt sea 'mp3'
        if fmt in ('mp3', 'flac', 'wav', 'aac', 'm4a'):
            for e in ('.mp3', '.flac', '.wav', '.aac', '.m4a', '.opus', '.ogg'):
                exts.add(e)
        else:
            for e in ('.mp4', '.mkv', '.avi', '.webm', '.mov'):
                exts.add(e)

        title_clean = title.lower()[:60]

        # Buscar por coincidencia de nombre
        for f in self.download_folder.iterdir():
            if f.suffix.lower() in exts:
                if (title_clean in f.stem.lower() or
                        f.stem.lower() in title_clean):
                    return str(f)

        # Fallback: archivo más reciente con extensión correcta
        candidates = []
        for e in exts:
            candidates.extend(self.download_folder.glob(f'*{e}'))
        if candidates:
            return str(max(candidates, key=lambda x: x.stat().st_ctime))

        return None

    def _write_json(self, file_path: str, meta: dict):
        """Guarda sidecar JSON con todos los metadatos."""
        try:
            json_path = Path(file_path).with_suffix('.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f'[Downloader] Error escribiendo JSON: {e}')
