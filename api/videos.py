import requests
import json
import re
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to allow imports from any location
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def normalize_view_count(view_count_str):
    """
    Convert view count string to integer.
    Examples: "11,268 views" -> 11268, "1.2M views" -> 1200000
    MySQL data type: INT (for views < 2.1B) or BIGINT (for larger values)
    """
    if not view_count_str:
        return None
    
    # Remove "views" and whitespace
    view_count_str = view_count_str.lower().replace('views', '').replace('view', '').strip()
    
    # Handle abbreviated numbers (K, M, B)
    multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000}
    
    for suffix, multiplier in multipliers.items():
        if suffix in view_count_str:
            number = float(view_count_str.replace(suffix, '').replace(',', '').strip())
            return int(number * multiplier)
    
    # Handle regular numbers with commas
    view_count_str = view_count_str.replace(',', '')
    
    try:
        return int(view_count_str)
    except ValueError:
        return None


def normalize_published_time(published_time_str, reference_time=None):
    """
    Convert relative time string to MySQL DATETIME format.
    Examples: "1 month ago" -> "2024-10-27 19:13:15"
              "2 days ago" -> "2024-11-25 19:13:15"
    MySQL data type: DATETIME
    
    Args:
        published_time_str: String like "1 month ago", "2 days ago", etc.
        reference_time: Optional datetime to use as reference (defaults to now)
    
    Returns:
        String in MySQL DATETIME format: "YYYY-MM-DD HH:MM:SS"
    """
    if not published_time_str:
        return None
    
    if reference_time is None:
        reference_time = datetime.now()
    
    # Parse the time string
    published_time_str = published_time_str.lower().strip()
    
    # Extract number and unit
    match = re.match(r'(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago', published_time_str)
    
    if not match:
        return None
    
    value = int(match.group(1))
    unit = match.group(2)
    
    # Calculate the timedelta
    if unit == 'second':
        delta = timedelta(seconds=value)
    elif unit == 'minute':
        delta = timedelta(minutes=value)
    elif unit == 'hour':
        delta = timedelta(hours=value)
    elif unit == 'day':
        delta = timedelta(days=value)
    elif unit == 'week':
        delta = timedelta(weeks=value)
    elif unit == 'month':
        # Approximate: 30 days per month
        delta = timedelta(days=value * 30)
    elif unit == 'year':
        # Approximate: 365 days per year
        delta = timedelta(days=value * 365)
    else:
        return None
    
    # Calculate the actual datetime
    published_datetime = reference_time - delta
    
    # Return in MySQL DATETIME format
    return published_datetime.strftime('%Y-%m-%d %H:%M:%S')


def get_videos(channel_id, save_to_db=None):
    """
    Fetch videos from a YouTube channel
    
    Args:
        channel_id: YouTube channel ID
        save_to_db: If True, save videos to database. If None, uses SAVE_TO_DB env var
        
    Returns:
        List of video dictionaries
    """
    # Use environment variable if save_to_db not explicitly set
    if save_to_db is None:
        from dotenv import load_dotenv
        load_dotenv()
        save_to_db = os.getenv('SAVE_TO_DB', 'false').lower() == 'true'
    
    headers = {
        'content-type': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'origin': 'https://www.youtube.com',
        'referer': 'https://www.youtube.com/',
    }

    json_data = {
        'context': {
            'client': {
                'clientName': 'WEB',
                'clientVersion': '2.20251125.06.00',
            },
        },
        'browseId': channel_id,
        'params': 'EgZ2aWRlb3PyBgQKAjoA',
    }

    try:
        response = requests.post(
            'https://www.youtube.com/youtubei/v1/browse',
            headers=headers,
            json=json_data,
        )
        response.raise_for_status()
        data = response.json()
        
        extracted_videos = []
        
        # Navigate to the tabs
        tabs = data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])
        
        for tab in tabs:
            # Find the selected tab (which should be Videos due to params)
            if tab.get('tabRenderer', {}).get('selected'):
                content = tab.get('tabRenderer', {}).get('content')
                if content and 'richGridRenderer' in content:
                    items = content['richGridRenderer'].get('contents', [])
                    
                    for item in items:
                        if 'richItemRenderer' in item:
                            video = item['richItemRenderer'].get('content', {}).get('videoRenderer', {})
                            if video:
                                video_id = video.get('videoId')
                                published_time_raw = video.get('publishedTimeText', {}).get('simpleText')
                                view_count_raw = video.get('viewCountText', {}).get('simpleText')
                                
                                # Normalize the data
                                published_time = normalize_published_time(published_time_raw)
                                view_count = normalize_view_count(view_count_raw)
                                
                                video_info = {
                                    'video_id': video_id,
                                    'channel_id': channel_id,
                                    'published_time': published_time,  # MySQL DATETIME format
                                    'view_count': view_count,  # Integer
                                    # Keep raw values for reference (optional)
                                    'published_time_raw': published_time_raw,
                                    'view_count_raw': view_count_raw
                                }
                                extracted_videos.append(video_info)
                break
        
        # Save to database if requested
        if save_to_db and extracted_videos:
            try:
                from database import VideoRepository
                # Ensure video items include channel_id for DB upsert
                stats = VideoRepository.upsert_videos_batch(extracted_videos)
                print(f"Database save completed: {stats} videos processed")
            except Exception as db_error:
                print(f"Error saving to database: {db_error}")
                # Continue execution even if database save fails
        
        return extracted_videos

    except Exception as e:
        print(f"Error fetching videos: {e}")
        return []

if __name__ == "__main__":
    channel_id = 'UCnwxzpFzZNtLH8NgTeAROFA'
    videos = get_videos(channel_id)
    print(json.dumps(videos, indent=2))