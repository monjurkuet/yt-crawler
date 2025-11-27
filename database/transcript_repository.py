"""
Database operations for storing YouTube transcripts

This repository handles transcripts CRUD and queries for missing transcripts
used by the transcript fetcher script.
"""

from database.db_manager import get_db_cursor, logger
from mysql.connector import Error, IntegrityError
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


class TranscriptRepository:
    """Repository for transcripts table operations"""

    @staticmethod
    def create_table():
        """Create transcripts table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS transcripts (
            video_id VARCHAR(20) PRIMARY KEY,
            transcript_raw LONGTEXT,
            status VARCHAR(20) DEFAULT 'fetched',
            error_message TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_transcript_video FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE,
            INDEX idx_status (status),
            INDEX idx_fetched_at (fetched_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """

        try:
            with get_db_cursor() as cursor:
                cursor.execute(create_table_query)
                logger.info("Transcripts table created or already exists")
                return True
        except Error as e:
            logger.error(f"Error creating transcripts table: {e}")
            raise

    @staticmethod
    def upsert_transcript(video_id: str, transcript_raw: Optional[Dict[str, Any]] = None, status: str = 'fetched', error_message: Optional[str] = None) -> bool:
        """Insert or update raw transcript data for a video.

        Stores only the raw transcript payload (list of snippet dicts) and status/error metadata.
        """
        upsert_query = """
        INSERT INTO transcripts (video_id, transcript_raw, status, error_message)
        VALUES (%(video_id)s, %(transcript_raw)s, %(status)s, %(error_message)s)
        ON DUPLICATE KEY UPDATE
            transcript_raw = VALUES(transcript_raw),
            status = VALUES(status),
            error_message = VALUES(error_message),
            fetched_at = CURRENT_TIMESTAMP
        """

        params = {
            'video_id': video_id,
            'transcript_raw': json.dumps(transcript_raw) if transcript_raw is not None else None,
            'status': status,
            'error_message': error_message,
        }

        try:
            with get_db_cursor() as cursor:
                cursor.execute(upsert_query, params)
                logger.info(f"Upserted transcript for video: {video_id} (status={status})")
                return True
        except Error as e:
            logger.error(f"Error upserting transcript for {video_id}: {e}")
            raise

    @staticmethod
    def get_transcript(video_id: str) -> Optional[Dict[str, Any]]:
        select_query = "SELECT * FROM transcripts WHERE video_id = %s"
        try:
            with get_db_cursor() as cursor:
                cursor.execute(select_query, (video_id,))
                return cursor.fetchone()
        except Error as e:
            logger.error(f"Error retrieving transcript for {video_id}: {e}")
            raise

    @staticmethod
    def get_videos_without_transcripts(limit: int = 100, offset: int = 0) -> List[str]:
        """Return a list of video_ids that don't yet have a transcript stored."""
        query = """
        SELECT v.video_id FROM videos v
        LEFT JOIN transcripts t ON v.video_id = t.video_id
        WHERE t.video_id IS NULL
        ORDER BY v.published_time DESC
        LIMIT %s OFFSET %s
        """

        try:
            with get_db_cursor() as cursor:
                cursor.execute(query, (limit, offset))
                rows = cursor.fetchall()
                return [r['video_id'] for r in rows]
        except Error as e:
            logger.error(f"Error fetching videos without transcripts: {e}")
            raise
