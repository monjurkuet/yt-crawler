"""
Fetch transcripts for videos stored in the database and persist them to a transcripts table.

Requirements: install youtube-transcript-api (added to requirements.txt)

Usage examples:
  python scrape_transcripts.py --create-table
  python scrape_transcripts.py --limit 50
  python scrape_transcripts.py --video-id VIDEO_ID
"""

import argparse
import json
import logging
from typing import List

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (  # type: ignore
    TranscriptsDisabled,
    NoTranscriptFound,
)

from database import init_database, close_database, TranscriptRepository


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_transcript_for_video(video_id: str, languages: List[str] = None) -> dict:
    """Fetch transcript for a single video id and return a result dictionary."""
    try:
        api = YouTubeTranscriptApi()
        # Using instance.fetch(video_id) returns a FetchedTranscript object
        fetched = api.fetch(video_id) if languages is None else api.fetch(video_id, languages=languages)

        # Most useful for downstream storage is the raw snippet list:
        # fetched.to_raw_data() returns a list of dicts: [{text, start, duration}, ...]
        if hasattr(fetched, 'to_raw_data'):
            raw_list = fetched.to_raw_data()
        else:
            # Fallback: build raw list from snippets attribute
            snippets = getattr(fetched, 'snippets', [])
            raw_list = []
            for s in snippets:
                text = getattr(s, 'text', None) or (s.get('text') if isinstance(s, dict) else '')
                start = getattr(s, 'start', None) or (s.get('start') if isinstance(s, dict) else None)
                duration = getattr(s, 'duration', None) or (s.get('duration') if isinstance(s, dict) else None)
                raw_list.append({'text': text, 'start': start, 'duration': duration})

        return {
            'status': 'fetched',
            'raw': raw_list,
            'error': None
        }

    except TranscriptsDisabled as e:
        logger.warning(f"Transcripts disabled for {video_id}: {e}")
        return {'status': 'failed', 'raw': None, 'error': str(e)}
    except NoTranscriptFound as e:
        logger.info(f"No transcripts found for {video_id}: {e}")
        return {'status': 'empty', 'raw': None, 'error': str(e)}
    except Exception as e:  # broad catch for network/other API errors
        logger.error(f"Error fetching transcript for {video_id}: {e}")
        return {'status': 'failed', 'raw': None, 'error': str(e)}


def process_batch(limit: int = 50, offset: int = 0, languages: List[str] = None) -> dict:
    """Fetch transcripts for a batch of videos without transcripts in DB."""
    video_ids = TranscriptRepository.get_videos_without_transcripts(limit=limit, offset=offset)
    logger.info(f"Found {len(video_ids)} videos without transcripts (limit={limit}, offset={offset})")

    stats = {'processed': 0, 'fetched': 0, 'empty': 0, 'failed': 0}

    for vid in video_ids:
        stats['processed'] += 1
        result = fetch_transcript_for_video(vid, languages)
        TranscriptRepository.upsert_transcript(
            video_id=vid,
            transcript_raw=result.get('raw'),
            status=result.get('status'),
            error_message=result.get('error')
        )

        if result.get('status') == 'fetched':
            stats['fetched'] += 1
        elif result.get('status') == 'empty':
            stats['empty'] += 1
        else:
            stats['failed'] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description='Fetch transcripts for videos in database')
    parser.add_argument('--create-table', action='store_true', help='Create transcripts table in DB')
    parser.add_argument('--limit', type=int, default=50, help='Batch size (default: 50)')
    parser.add_argument('--offset', type=int, default=0, help='Offset for pagination')
    parser.add_argument('--video-id', type=str, default=None, help='Fetch transcript for single video id')
    parser.add_argument('--language', type=str, default=None, help='Preferred language code (e.g. en). Can pass comma-separated list')

    args = parser.parse_args()

    init_database()

    try:
        if args.create_table:
            TranscriptRepository.create_table()

        languages = None
        if args.language:
            languages = [l.strip() for l in args.language.split(',') if l.strip()]

        if args.video_id:
            logger.info(f"Fetching transcript for single video: {args.video_id}")
            res = fetch_transcript_for_video(args.video_id, languages)
            TranscriptRepository.upsert_transcript(
                video_id=args.video_id,
                transcript_raw=res.get('raw'),
                status=res.get('status'),
                error_message=res.get('error')
            )
            logger.info(f"Result: {res}")
        else:
            stats = process_batch(limit=args.limit, offset=args.offset, languages=languages)
            logger.info(f"Batch completed: {stats}")

    finally:
        close_database()


if __name__ == '__main__':
    main()
