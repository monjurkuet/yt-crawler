import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import logging
import pymongo
import json

load_dotenv()
api_key = os.getenv('API_KEY')

# MongoDB connection
mongodb_connection_string = os.getenv('MONGODB_CONNECTION')
if not mongodb_connection_string:
    logging.error("MONGODB_CONNECTION environment variable not set.")
    pass 

client = None
if mongodb_connection_string:
    try:
        client = pymongo.MongoClient(mongodb_connection_string)
        db = client['cryptoproject'] # Access the 'cryptoproject' database
        yt_videos_collection = db['yt_videos'] # Access the 'yt_videos' collection
        logging.info("MongoDB connected successfully.")
    except pymongo.errors.ConnectionFailure as e:
        logging.error(f"Could not connect to MongoDB: {e}")
        client = None # Ensure client is None if connection fails

# Initialize the YouTube Data API client
youtube = build('youtube', 'v3', developerKey=api_key)

logging.info("YouTube API service initialized.")

# Function to process a single channel
def process_channel(channel_id):
    logging.info(f"Processing channel ID: {channel_id}")
    try:
        # Call the search.list method to retrieve the latest video
        search_response = youtube.search().list(
            channelId=channel_id,
            type='video',
            order='date', # Order by date to get the latest videos
            part='id,snippet',
            maxResults=5  # Change maxResults to 5
        ).execute()

        # Extract video details for the last 5 videos
        if search_response.get('items'):
            print(f"Last 5 Videos for Channel ID: {channel_id}\n")
            for i, video_item in enumerate(search_response['items'], 1):
                video_id = video_item['id']['videoId']
                video_title = video_item['snippet']['title']
                video_published_at = video_item['snippet']['publishedAt']
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                print(f"--- Video {i} ---")
                print(f"Title: {video_title}")
                print(f"Video ID: {video_id}")
                print(f"Published At: {video_published_at}")
                print(f"Video URL: {video_url}\n")
                # print(json.dumps(video_item, indent=2)) # Reduced verbosity

                # Save the found video item to MongoDB
                if client:
                    try:
                        # Use update_one with upsert=True to avoid duplicates if running multiple times
                        yt_videos_collection.update_one(
                            {'id.videoId': video_id},
                            {'$set': video_item},
                            upsert=True
                        )
                        logging.info(f"Successfully saved/updated video {video_id} to MongoDB.")
                    except Exception as mongo_e:
                        logging.error(f"Failed to save video {video_id} to MongoDB: {mongo_e}")
                else:
                    logging.warning("MongoDB client not initialized, skipping database save.")
        else:
            print(f"No videos found for channel ID: {channel_id}")

    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred for channel {channel_id}: {e.content.decode()}")
    except Exception as e:
        print(f"An unexpected error occurred for channel {channel_id}: {e}")

# Main execution
channels_file = os.path.join(os.path.dirname(__file__), 'channels_latest_tomonitor.txt')

try:
    if os.path.exists(channels_file):
        with open(channels_file, 'r') as f:
            channel_ids = [line.strip() for line in f if line.strip()]
        
        if channel_ids:
            for channel_id in channel_ids:
                process_channel(channel_id)
        else:
            logging.warning(f"No channel IDs found in {channels_file}")
    else:
        logging.error(f"Channels file not found: {channels_file}")
        # Fallback to the default single channel if file is missing (optional, but good for testing)
        # default_channel_id = "UCnwxzpFzZNtLH8NgTeAROFA"
        # process_channel(default_channel_id)

finally:
    if client:
        client.close()
        logging.info("MongoDB connection closed.")