"""Utilidades comunes"""
from pathlib import Path


def format_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f'{m}:{s:02d}'


def truncate_text(text: str, max_len: int = 50) -> str:
    if len(text) > max_len:
        return text[:max_len - 3] + '...'
    return text


def clean_filename(name: str) -> str:
    for ch in '<>:"/\\|?*':
        name = name.replace(ch, '')
    return name.strip()


def get_file_type(file_path: str) -> str:
    from config import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS
    ext = Path(file_path).suffix.lower()
    if ext in AUDIO_EXTENSIONS:
        return 'audio'
    if ext in VIDEO_EXTENSIONS:
        return 'video'
    return 'unknown'
