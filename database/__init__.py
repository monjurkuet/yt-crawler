"""
Database package initialization
"""

from .db_manager import (
    db_manager,
    init_database,
    close_database,
    get_db_connection,
    get_db_cursor
)

from .video_repository import VideoRepository
from .transcript_repository import TranscriptRepository

__all__ = [
    'db_manager',
    'init_database',
    'close_database',
    'get_db_connection',
    'get_db_cursor',
    'VideoRepository',
    'TranscriptRepository'
]
