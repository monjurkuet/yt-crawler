"""
Batch scrape channels from a file and insert their videos into the database.

Usage examples:
  python scrape_channels.py --channels-file channels.txt --create-table --save-to-db

The file should contain one channel ID per line. Blank lines and lines starting
with '#' are ignored.
"""

import argparse
import sys
import os
import time
from typing import List

# Add parent directory to path so this script can run from the repo root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.videos import get_videos
from database import init_database, close_database, VideoRepository


def parse_channel_file(file_path: str) -> List[str]:
    """Parse a channel file and return channel IDs.

    Ignores blank lines and lines that start with '#'.
    """
    channels = []
    with open(file_path, 'r', encoding='utf-8') as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            channels.append(line)
    return channels


def main():
    parser = argparse.ArgumentParser(description='Batch scrape YouTube channels from a file')
    parser.add_argument('--channels-file', '-f', default='channels.txt', help='Path to the channel ids text file')
    parser.add_argument('--create-table', action='store_true', help='Create the videos table if it does not exist')
    parser.add_argument('--save-to-db', dest='save_to_db', action='store_true', help='Save results to DB (overrides env SAVE_TO_DB)')
    parser.add_argument('--no-save', dest='save_to_db', action='store_false', help="Don't save to DB")
    parser.set_defaults(save_to_db=None)
    parser.add_argument('--delay', type=float, default=0.0, help='Seconds to wait between channel requests (default 0)')

    args = parser.parse_args()

    if not os.path.exists(args.channels_file):
        print(f"Channel file not found: {args.channels_file}")
        raise SystemExit(1)

    channels = parse_channel_file(args.channels_file)
    if not channels:
        print('No channels found in file. Nothing to do.')
        return

    # Initialize DB only if needed (create table or save_to_db enabled via flag or env)
    env_save = os.getenv('SAVE_TO_DB', 'false').lower() == 'true'
    need_db = bool(args.create_table or args.save_to_db is True or (args.save_to_db is None and env_save))

    if need_db:
        print('Initializing database...')
        init_database()

    if args.create_table:
        print('Ensuring videos table exists...')
        VideoRepository.create_table()

    total_channels = 0
    total_videos_fetched = 0
    total_videos_saved = 0

    try:
        for channel in channels:
            total_channels += 1
            try:
                print(f"\nProcessing channel ({total_channels}/{len(channels)}): {channel}")
                # Decide how to handle DB writes so we don't upsert twice
                if args.save_to_db is True:
                    # Fetch without letting get_videos write, we'll upsert here to get counts
                    videos = get_videos(channel, save_to_db=False)
                else:
                    # Pass through explicit False or None to allow env-controlled behavior
                    videos = get_videos(channel, save_to_db=args.save_to_db)
                fetched = len(videos)
                total_videos_fetched += fetched
                print(f"Fetched {fetched} videos for channel {channel}")

                # If get_videos didn't save to DB, we can optionally upsert here
                if args.save_to_db is False:
                    print('Skipping DB save (explicitly disabled)')
                elif args.save_to_db is True:
                    # We fetched with save_to_db=False above, so upsert here and count results
                    try:
                        count = VideoRepository.upsert_videos_batch(videos) if videos else 0
                        total_videos_saved += count
                        print(f'Upserted {count} videos')
                    except Exception as e:
                        print(f'Error upserting videos for {channel}: {e}')
                else:
                    # save_to_db was not explicitly set -> get_videos used env var. We don't double-upsert.
                    print('DB save controlled by environment variable (SAVE_TO_DB)')

            except Exception as ce:
                print(f"Error processing channel {channel}: {ce}")

            if args.delay and args.delay > 0:
                time.sleep(args.delay)

    finally:
        print('\nBatch run complete.')
        print(f'Total channels: {total_channels}')
        print(f'Total videos fetched: {total_videos_fetched}')
        print(f'Total videos saved/upserted (counted): {total_videos_saved}')
        if need_db:
            print('Closing database...')
            close_database()


if __name__ == '__main__':
    main()
