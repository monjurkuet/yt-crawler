import time
import datetime
import json
import logging
from tqdm.notebook import tqdm
import sys
import mysql.connector # Import explicitly for error handling
from googleapiclient.errors import HttpError # Import for specific YouTube API error handling

from config_manager import ConfigManager
from youtube_client import YouTubeClient, YouTubeVideoParser
from db_connector import DBConnector

class DataIngestor:
    def __init__(self):
        self.config = ConfigManager()
        self.youtube_client = YouTubeClient()
        self.db_connector = DBConnector()
        self.logger = self._setup_logging()

        self.insert_video_sql = """
INSERT IGNORE INTO youtube_videos (
    video_id, channel_id, published_at, title, description, tags,
    category_id, default_language, duration, caption, view_count, like_count, comment_count
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
);
"""

    def _setup_logging(self):
        logger = logging.getLogger('video_processor')
        logger.setLevel(logging.INFO)

        # Clear existing handlers to prevent duplicate output if called multiple times
        if logger.handlers:
            for handler in list(logger.handlers):
                logger.removeHandler(handler)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # Handler for successful insertions
        success_handler = logging.FileHandler('inserted_video_ids.log')
        success_handler.setLevel(logging.INFO)
        success_handler.setFormatter(formatter)
        logger.addHandler(success_handler)

        # Handler for errors
        error_handler = logging.FileHandler('error_log.log')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def _read_video_ids_from_file(self):
        video_ids = []
        file_path = self.config.VIDEO_IDS_FILE_PATH
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    video_id = line.strip()
                    if video_id:
                        video_ids.append(video_id)
            self.logger.info(f"Successfully read {len(video_ids)} video IDs from {file_path}")
        except FileNotFoundError:
            self.logger.error(f"Error: The file '{file_path}' was not found.")
        except Exception as e:
            self.logger.error(f"An error occurred while reading the file: {e}")
        return video_ids

    def ingest_data(self):
        video_ids = self._read_video_ids_from_file()
        if not video_ids:
            self.logger.error("No video IDs to process. Exiting.")
            return

        processed_count = 0
        inserted_count = 0
        error_count = 0

        self.logger.info("Attempting to establish database connection...")
        if not self.db_connector.establish_connection():
            self.logger.critical("Failed to establish database connection after multiple retries. Aborting data ingestion.")
            return

        # Ensure the table exists
        self.logger.info("Ensuring database table exists...")
        self.db_connector.create_table()

        cursor = None # Explicitly initialize cursor
        try:
            cursor = self.db_connector.mysql_conn.cursor()
            self.logger.info(f"Processing {len(video_ids)} video IDs...")
            for video_id in tqdm(video_ids, desc="Processing Videos"):
                processed_count += 1
                try:
                    raw_video_data = self.youtube_client.get_video_data(video_id)
                    time.sleep(0.2)  # Introduce a small delay for rate limiting

                    if raw_video_data is None:
                        # This case is already logged by youtube_client if 'No video found'
                        # or if an unrecoverable error occurred. Just increment error count.
                        self.logger.error(f"Skipping video ID {video_id} due to failed data fetch or parsing.")
                        error_count += 1
                        continue

                    parser = YouTubeVideoParser(raw_video_data)
                    parsed_data = parser.parse_data()

                    if not parsed_data:
                        self.logger.error(f"Failed to parse data for video ID: {video_id}. Skipping.")
                        error_count += 1
                        continue

                    # Prepare data for MySQL insertion
                    video_id_val = video_id
                    channel_id_val = parsed_data.get('channelId')
                    published_at_val = None
                    if parsed_data.get('publishedAt'):
                        try:
                            # Convert ISO 8601 string to datetime object
                            published_at_val = datetime.datetime.fromisoformat(parsed_data['publishedAt'].replace('Z', '+00:00'))
                        except ValueError:
                            self.logger.warning(f"Could not parse publishedAt for {video_id}: {parsed_data['publishedAt']}")

                    title_val = parsed_data.get('title')
                    description_val = parsed_data.get('description')
                    tags_val = json.dumps(parsed_data.get('tags', [])) # Convert tags list to JSON string
                    category_id_val = parsed_data.get('categoryId')
                    default_language_val = parsed_data.get('defaultLanguage')
                    duration_val = parsed_data.get('duration')
                    caption_val = 1 if parsed_data.get('caption') == 'true' else 0

                    view_count_val = int(parsed_data['viewCount']) if parsed_data.get('viewCount') else None
                    like_count_val = int(parsed_data['likeCount']) if parsed_data.get('likeCount') else None
                    comment_count_val = int(parsed_data['commentCount']) if parsed_data.get('commentCount') else None

                    video_data_tuple = (
                        video_id_val, channel_id_val, published_at_val, title_val, description_val, tags_val,
                        category_id_val, default_language_val, duration_val, caption_val,
                        view_count_val, like_count_val, comment_count_val
                    )

                    cursor.execute(self.insert_video_sql, video_data_tuple)
                    self.db_connector.mysql_conn.commit()
                    self.logger.info(f"Successfully inserted video ID: {video_id}")
                    inserted_count += 1

                except mysql.connector.Error as db_err:
                    if db_err.errno == 1062:
                        self.logger.warning(f"Video ID {video_id} already exists in database. Skipping insertion. Error: {db_err}")
                        inserted_count += 1
                    else:
                        self.logger.error(f"Database error for video ID {video_id}: {db_err}")
                        error_count += 1
                except HttpError as http_err:
                    self.logger.error(f"YouTube API HTTP error for video ID {video_id}: {http_err} - Details: {http_err.content.decode('utf-8')}")
                    error_count += 1
                except Exception as e:
                    self.logger.error(f"Unexpected error processing video ID {video_id}: {e}")
                    error_count += 1

        except Exception as final_e:
            self.logger.critical(f"An unexpected critical error occurred during video processing loop: {final_e}")
        finally:
            if cursor:
                cursor.close()
            self.db_connector.close_connection()

        self.logger.info("\n--- Processing Summary ---")
        self.logger.info(f"Total video IDs from file: {len(video_ids)}")
        self.logger.info(f"Total processed attempts: {processed_count}")
        self.logger.info(f"Successfully inserted (or already existed): {inserted_count}")
        self.logger.info(f"Errors encountered: {error_count}")
        self.logger.info("Check 'inserted_video_ids.log' for successful insertions.")
        self.logger.info("Check 'error_log.log' for detailed error information.")

# Example usage
if __name__ == '__main__':
    ingestor = DataIngestor()
    ingestor.ingest_data()
