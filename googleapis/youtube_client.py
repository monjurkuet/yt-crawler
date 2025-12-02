import googleapiclient.discovery
from googleapiclient.errors import HttpError # Import HttpError
from config_manager import ConfigManager
import logging
from tenacity import ( # Import tenacity components
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_exception,
    after_log
)

class YouTubeClient:
    def __init__(self):
        self.config = ConfigManager()
        self.api_key = self.config.API_KEY
        self.youtube = googleapiclient.discovery.build(
            'youtube', 'v3', developerKey=self.api_key
        )
        self.logger = self._setup_logging() # Setup logger for the client

    def _setup_logging(self):
        logger = logging.getLogger('youtube_client')
        if not logger.handlers: # Prevent adding multiple handlers
            handler = logging.StreamHandler() # Or a file handler
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _is_5xx_or_429(self, exception):
        """Helper to determine if an HttpError is a 5xx server error or 429 rate limit error."""
        return isinstance(exception, HttpError) and \
               (exception.resp.status >= 500 or exception.resp.status == 429)

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(HttpError) & retry_if_exception(_is_5xx_or_429),
        after=after_log(logging.getLogger('youtube_client'), logging.WARNING)
    )
    def get_video_data(self, video_id):
        try:
            request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics,topicDetails,status,player,recordingDetails,liveStreamingDetails,localizations",
                id=video_id
            )
            response = request.execute()

            if response['items']:
                return response['items'][0]
            else:
                self.logger.warning(f"No video found with ID: {video_id}")
                return None

        except HttpError as e:
            self.logger.error(f"HTTP error for video ID {video_id}: {e} - Details: {e.content.decode('utf-8')}")
            raise # Re-raise to trigger retry
        except Exception as e:
            self.logger.error(f"An unexpected error occurred for video ID {video_id}: {e}")
            return None

class YouTubeVideoParser:
    def __init__(self, video_data):
        self.video_data = video_data

    def parse_data(self):
        if not self.video_data:
            return {}

        parsed_info = {
            'channelId': self.video_data.get('snippet', {}).get('channelId'),
            'publishedAt': self.video_data.get('snippet', {}).get('publishedAt'),
            'title': self.video_data.get('snippet', {}).get('title'),
            'description': self.video_data.get('snippet', {}).get('description'),
            'tags': self.video_data.get('snippet', {}).get('tags', []), # Default to empty list if no tags
            'categoryId': self.video_data.get('snippet', {}).get('categoryId'),
            'defaultLanguage': self.video_data.get('snippet', {}).get('defaultLanguage'),
            'duration': self.video_data.get('contentDetails', {}).get('duration'),
            'caption': self.video_data.get('contentDetails', {}).get('caption'),
            'viewCount': self.video_data.get('statistics', {}).get('viewCount'),
            'likeCount': self.video_data.get('statistics', {}).get('likeCount'),
            'commentCount': self.video_data.get('statistics', {}).get('commentCount')
        }
        return parsed_info

# Example usage
if __name__ == '__main__':
    # This part would typically be used in data_ingestor, not run directly here
    print("YouTubeClient and YouTubeVideoParser classes defined with enhanced error handling.")
