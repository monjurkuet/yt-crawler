"""
Example usage of the YouTube crawler with database integration
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.videos import get_videos
from database import init_database, close_database, VideoRepository


def main():
    """Main function demonstrating database integration"""
    
    print("=" * 60)
    print("YouTube Crawler - Database Integration Example")
    print("=" * 60)
    
    try:
        # Step 1: Initialize database connection
        print("\n[1/4] Initializing database connection...")
        init_database()
        print("✓ Database connection established")
        
        # Step 2: Create table if it doesn't exist
        print("\n[2/4] Creating database table...")
        VideoRepository.create_table()
        print("✓ Table created or already exists")
        
        # Step 3: Fetch and save videos
        # Note: save_to_db is controlled by SAVE_TO_DB in .env
        # You can override it by passing save_to_db=True/False explicitly
        channel_id = 'UCnwxzpFzZNtLH8NgTeAROFA'
        print(f"\n[3/4] Fetching videos from channel: {channel_id}")
        videos = get_videos(channel_id)  # Uses SAVE_TO_DB from .env
        print(f"✓ Fetched and saved {len(videos)} videos")
        
        # Step 4: Display statistics
        print("\n[4/4] Database statistics:")
        total_videos = VideoRepository.get_video_count()
        print(f"✓ Total videos in database: {total_videos}")
        
        # Display sample videos
        print("\n" + "=" * 60)
        print("Sample Videos (first 5):")
        print("=" * 60)
        sample_videos = VideoRepository.get_all_videos(limit=5)
        for i, video in enumerate(sample_videos, 1):
            print(f"\n{i}. Video ID: {video['video_id']}")
            # channel_id may be present in schema after migration
            if 'channel_id' in video:
                print(f"   Channel: {video['channel_id']}")
            print(f"   Published: {video['published_time']}")
            print(f"   Views: {video['view_count']:,}")
            print(f"   Raw: {video['published_time_raw']} | {video['view_count_raw']}")
        
        print("\n" + "=" * 60)
        print("✓ Process completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Always close database connection
        print("\nClosing database connection...")
        close_database()
        print("✓ Database connection closed")


if __name__ == "__main__":
    main()
