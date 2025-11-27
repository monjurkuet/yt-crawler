"""
Database operations for YouTube videos
Handles CRUD operations with proper error handling and transactions
"""

from database.db_manager import get_db_cursor, logger
from mysql.connector import Error, IntegrityError
from typing import List, Dict, Any, Optional
from datetime import datetime


class VideoRepository:
    """Repository pattern for video database operations"""
    
    @staticmethod
    def create_table():
        """Create videos table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS videos (
            video_id VARCHAR(20) PRIMARY KEY,
            channel_id VARCHAR(64) NOT NULL,
            published_time DATETIME NOT NULL,
            view_count INT UNSIGNED NOT NULL,
            published_time_raw VARCHAR(50),
            view_count_raw VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_channel_id (channel_id),
            INDEX idx_published_time (published_time),
            INDEX idx_view_count (view_count),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        try:
            with get_db_cursor() as cursor:
                cursor.execute(create_table_query)
                logger.info("Videos table created or already exists")
                return True
        except Error as e:
            logger.error(f"Error creating videos table: {e}")
            raise
    
    @staticmethod
    def insert_video(video_data: Dict[str, Any]) -> bool:
        """
        Insert a single video into the database
        
        Args:
            video_data: Dictionary containing video information
            
        Returns:
            bool: True if successful, False otherwise
        """
        insert_query = """
        INSERT INTO videos (
            video_id, channel_id, published_time, view_count, 
            published_time_raw, view_count_raw
        ) VALUES (
            %(video_id)s, %(channel_id)s, %(published_time)s, %(view_count)s,
            %(published_time_raw)s, %(view_count_raw)s
        )
        """
        
        try:
            with get_db_cursor() as cursor:
                cursor.execute(insert_query, video_data)
                logger.info(f"Inserted video: {video_data['video_id']}")
                return True
        except IntegrityError as e:
            logger.warning(f"Video {video_data['video_id']} already exists: {e}")
            return False
        except Error as e:
            logger.error(f"Error inserting video {video_data['video_id']}: {e}")
            raise
    
    @staticmethod
    def insert_videos_batch(videos: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Insert multiple videos in a single transaction
        
        Args:
            videos: List of video dictionaries
            
        Returns:
            Dict with counts of inserted, skipped, and failed videos
        """
        insert_query = """
        INSERT INTO videos (
            video_id, channel_id, published_time, view_count, 
            published_time_raw, view_count_raw
        ) VALUES (
            %(video_id)s, %(channel_id)s, %(published_time)s, %(view_count)s,
            %(published_time_raw)s, %(view_count_raw)s
        )
        """
        
        stats = {'inserted': 0, 'skipped': 0, 'failed': 0}
        
        try:
            with get_db_cursor() as cursor:
                for video in videos:
                    try:
                        cursor.execute(insert_query, video)
                        stats['inserted'] += 1
                        logger.debug(f"Inserted video: {video['video_id']}")
                    except IntegrityError:
                        stats['skipped'] += 1
                        logger.debug(f"Skipped duplicate video: {video['video_id']}")
                    except Error as e:
                        stats['failed'] += 1
                        logger.error(f"Failed to insert video {video['video_id']}: {e}")
                
                logger.info(f"Batch insert completed: {stats}")
                return stats
        except Error as e:
            logger.error(f"Error during batch insert: {e}")
            raise
    
    @staticmethod
    def update_video(video_id: str, video_data: Dict[str, Any]) -> bool:
        """
        Update an existing video
        
        Args:
            video_id: Video ID to update
            video_data: Dictionary containing updated video information
            
        Returns:
            bool: True if successful, False otherwise
        """
        update_query = """
        UPDATE videos 
        SET published_time = %(published_time)s,
            view_count = %(view_count)s,
            published_time_raw = %(published_time_raw)s,
            view_count_raw = %(view_count_raw)s,
            channel_id = %(channel_id)s
        WHERE video_id = %(video_id)s
        """
        
        try:
            video_data['video_id'] = video_id
            with get_db_cursor() as cursor:
                cursor.execute(update_query, video_data)
                if cursor.rowcount > 0:
                    logger.info(f"Updated video: {video_id}")
                    return True
                else:
                    logger.warning(f"Video not found for update: {video_id}")
                    return False
        except Error as e:
            logger.error(f"Error updating video {video_id}: {e}")
            raise
    
    @staticmethod
    def upsert_video(video_data: Dict[str, Any]) -> bool:
        """
        Insert or update a video (INSERT ... ON DUPLICATE KEY UPDATE)
        
        Args:
            video_data: Dictionary containing video information
            
        Returns:
            bool: True if successful, False otherwise
        """
        upsert_query = """
        INSERT INTO videos (
            video_id, channel_id, published_time, view_count, 
            published_time_raw, view_count_raw
        ) VALUES (
            %(video_id)s, %(channel_id)s, %(published_time)s, %(view_count)s,
            %(published_time_raw)s, %(view_count_raw)s
        )
        ON DUPLICATE KEY UPDATE
            view_count = VALUES(view_count),
            view_count_raw = VALUES(view_count_raw),
            channel_id = VALUES(channel_id)
        """
        
        try:
            with get_db_cursor() as cursor:
                cursor.execute(upsert_query, video_data)
                logger.info(f"Upserted video: {video_data['video_id']}")
                return True
        except Error as e:
            logger.error(f"Error upserting video {video_data['video_id']}: {e}")
            raise
    
    @staticmethod
    def upsert_videos_batch(videos: List[Dict[str, Any]]) -> int:
        """
        Upsert multiple videos in a single transaction
        
        Args:
            videos: List of video dictionaries
            
        Returns:
            int: Number of videos processed
        """
        upsert_query = """
        INSERT INTO videos (
            video_id, channel_id, published_time, view_count, 
            published_time_raw, view_count_raw
        ) VALUES (
            %(video_id)s, %(channel_id)s, %(published_time)s, %(view_count)s,
            %(published_time_raw)s, %(view_count_raw)s
        )
        ON DUPLICATE KEY UPDATE
            view_count = VALUES(view_count),
            view_count_raw = VALUES(view_count_raw),
            channel_id = VALUES(channel_id)
        """
        
        count = 0
        try:
            with get_db_cursor() as cursor:
                for video in videos:
                    cursor.execute(upsert_query, video)
                    count += 1
                
                logger.info(f"Upserted {count} videos")
                return count
        except Error as e:
            logger.error(f"Error during batch upsert: {e}")
            raise
    
    @staticmethod
    def get_video(video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single video by ID
        
        Args:
            video_id: Video ID to retrieve
            
        Returns:
            Dict containing video data or None if not found
        """
        select_query = "SELECT * FROM videos WHERE video_id = %s"
        
        try:
            with get_db_cursor() as cursor:
                cursor.execute(select_query, (video_id,))
                result = cursor.fetchone()
                return result
        except Error as e:
            logger.error(f"Error retrieving video {video_id}: {e}")
            raise
    
    @staticmethod
    def get_all_videos(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get all videos with pagination
        
        Args:
            limit: Maximum number of videos to return
            offset: Number of videos to skip
            
        Returns:
            List of video dictionaries
        """
        select_query = """
        SELECT * FROM videos 
        ORDER BY published_time DESC 
        LIMIT %s OFFSET %s
        """
        
        try:
            with get_db_cursor() as cursor:
                cursor.execute(select_query, (limit, offset))
                results = cursor.fetchall()
                return results
        except Error as e:
            logger.error(f"Error retrieving videos: {e}")
            raise
    
    @staticmethod
    def delete_video(video_id: str) -> bool:
        """
        Delete a video by ID
        
        Args:
            video_id: Video ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        delete_query = "DELETE FROM videos WHERE video_id = %s"
        
        try:
            with get_db_cursor() as cursor:
                cursor.execute(delete_query, (video_id,))
                if cursor.rowcount > 0:
                    logger.info(f"Deleted video: {video_id}")
                    return True
                else:
                    logger.warning(f"Video not found for deletion: {video_id}")
                    return False
        except Error as e:
            logger.error(f"Error deleting video {video_id}: {e}")
            raise
    
    @staticmethod
    def get_video_count() -> int:
        """
        Get total number of videos in database
        
        Returns:
            int: Total video count
        """
        count_query = "SELECT COUNT(*) as count FROM videos"
        
        try:
            with get_db_cursor() as cursor:
                cursor.execute(count_query)
                result = cursor.fetchone()
                return result['count'] if result else 0
        except Error as e:
            logger.error(f"Error counting videos: {e}")
            raise
