"""
Gestor de playlists — Tema Gótico
"""
import json
from pathlib import Path
from config import PLAYLISTS_FOLDER, AUDIO_EXTENSIONS, VIDEO_EXTENSIONS


class PlaylistManager:
    def __init__(self):
        self.playlists: dict = {}
        self.current_playlist: str = 'Mi Biblioteca'
        self._ensure_defaults()
        self.load_all()

    # ── Internos ──────────────────────────────────────────────────────────────
    def _ensure_defaults(self):
        if 'Mi Biblioteca' not in self.playlists:
            self.playlists['Mi Biblioteca'] = []

    # ── CRUD de playlists ─────────────────────────────────────────────────────
    def create_playlist(self, name: str) -> bool:
        if name not in self.playlists:
            self.playlists[name] = []
            self._save_playlist(name)
            return True
        return False

    def delete_playlist(self, name: str) -> bool:
        if name in self.playlists and name != 'Mi Biblioteca':
            del self.playlists[name]
            pf = PLAYLISTS_FOLDER / f'{name}.json'
            if pf.exists():
                pf.unlink()
            return True
        return False

    def rename_playlist(self, old: str, new: str) -> bool:
        if old in self.playlists and new not in self.playlists:
            self.playlists[new] = self.playlists.pop(old)
            (PLAYLISTS_FOLDER / f'{old}.json').unlink(missing_ok=True)
            self._save_playlist(new)
            return True
        return False

    def get_all_playlists(self) -> list:
        return list(self.playlists.keys())

    def set_current_playlist(self, name: str):
        self.current_playlist = name

    # ── CRUD de canciones ─────────────────────────────────────────────────────
    def add_song_to_playlist(self, playlist: str, file_path: str, metadata: dict = None) -> bool:
        if playlist not in self.playlists:
            self.create_playlist(playlist)
        for s in self.playlists[playlist]:
            if s.get('path') == file_path:
                return False
        entry = {
            'path':     file_path,
            'title':    (metadata or {}).get('title', Path(file_path).stem),
            'artist':   (metadata or {}).get('artist', 'Desconocido'),
            'duration': (metadata or {}).get('duration', 0),
        }
        self.playlists[playlist].append(entry)
        self._save_playlist(playlist)
        return True

    def remove_song_from_playlist(self, playlist: str, file_path: str) -> bool:
        if playlist in self.playlists:
            before = len(self.playlists[playlist])
            self.playlists[playlist] = [
                s for s in self.playlists[playlist] if s.get('path') != file_path
            ]
            if len(self.playlists[playlist]) < before:
                self._save_playlist(playlist)
                return True
        return False

    def get_playlist_songs(self, playlist: str) -> list:
        return self.playlists.get(playlist, [])

    # ── Persistencia ──────────────────────────────────────────────────────────
    def _save_playlist(self, name: str):
        try:
            PLAYLISTS_FOLDER.mkdir(parents=True, exist_ok=True)
            with open(PLAYLISTS_FOLDER / f'{name}.json', 'w', encoding='utf-8') as f:
                json.dump(self.playlists.get(name, []), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f'[Playlist] Error al guardar {name}: {e}')

    def load_all(self):
        self._ensure_defaults()
        try:
            for pf in PLAYLISTS_FOLDER.glob('*.json'):
                name = pf.stem
                with open(pf, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Filtrar canciones cuyo archivo aún existe
                self.playlists[name] = [
                    s for s in data if Path(s.get('path', '')).exists()
                ]
        except Exception as e:
            print(f'[Playlist] Error al cargar: {e}')
        self._ensure_defaults()

    def save_all(self):
        for name in self.playlists:
            self._save_playlist(name)
