# YouTube Crawler

A production-ready YouTube video crawler with MySQL database integration and SSH tunnel support.

## Features

✅ **Video Data Extraction**
- Fetch video metadata from YouTube channels
- Extract video ID, published time, and view count
- Normalize data for database storage

✅ **Database Integration**
- MySQL database support with SSH tunnel
- Connection pooling for performance
- Repository pattern for clean data access
- Batch operations for efficiency

✅ **Data Normalization**
- Convert relative time ("1 month ago") to MySQL DATETIME
- Convert view counts ("11,268 views") to integers
- Preserve raw data for reference

✅ **Best Practices**
✅ **Transcripts (raw only)**
- Fetch transcripts using youtube-transcript-api and store the raw snippet list returned by fetched_transcript.to_raw_data() into the `transcripts` table as JSON. The table stores only the raw data, fetch status, and any error message — extra metadata (combined text / language columns) is intentionally omitted to keep the storage minimal.

- Singleton pattern for resource management
- Context managers for automatic cleanup
- Comprehensive error handling
- Detailed logging
- Security-first approach

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run Example
```bash
python example_with_database.py
```

## Usage

### Basic Example
```python
from api.videos import get_videos
from database import init_database, close_database

# Initialize database
init_database()

# Fetch and save videos
channel_id = 'UCnwxzpFzZNtLH8NgTeAROFA'
videos = get_videos(channel_id, save_to_db=True)

# Close database
close_database()
```

### Advanced Example
```python
from database import VideoRepository, init_database

init_database()

# Create table
VideoRepository.create_table()

# Manual operations
video = VideoRepository.get_video('VIDEO_ID')
all_videos = VideoRepository.get_all_videos(limit=100)
count = VideoRepository.get_video_count()
```

### Batch scraping channels from a file

You can provide a text file containing channel IDs (one per line) and run a batch scraper
to fetch and optionally save videos for each channel:

```bash
# create a channels file (one ID per line) or use channels_sample.txt
python scrape_channels.py --channels-file channels_sample.txt --create-table --save-to-db
```

### Transcripts

This project includes a transcript fetcher which will read video IDs from the `videos` table and store transcripts in a new `transcripts` table.

Usage:

```bash
# Create the transcripts table in the configured database
python scrape_transcripts.py --create-table

# Fetch transcripts in batches (default limit 50):
python scrape_transcripts.py --limit 100

# Fetch transcripts for a single video by id:
python scrape_transcripts.py --video-id <VIDEO_ID> --language en
```

The script uses `youtube-transcript-api` so make sure to install dependencies:

```bash
pip install -r requirements.txt
```

Options:
- `--channels-file` : path to file with channel IDs (default: channels.txt)
- `--create-table` : create the videos table if missing
- `--save-to-db` / `--no-save` : explicitly save or skip DB saving (overrides SAVE_TO_DB env variable)
- `--delay` : optional delay between channel requests to reduce load


## Project Structure

```
yt-crawler/
├── api/
│   └── videos.py              # Video fetching and normalization
├── database/
│   ├── __init__.py            # Package exports
│   ├── db_manager.py          # Connection management
│   └── video_repository.py   # CRUD operations
├── .env.example               # Configuration template
├── requirements.txt           # Dependencies
├── example_with_database.py  # Usage example
├── DATABASE_GUIDE.md          # Full documentation
├── QUICKSTART.md              # Quick reference
└── IMPLEMENTATION_SUMMARY.md # Implementation details
```

## Database Schema

```sql
CREATE TABLE videos (
    video_id VARCHAR(20) PRIMARY KEY,
    channel_id VARCHAR(64) NOT NULL,
    published_time DATETIME NOT NULL,
    view_count INT UNSIGNED NOT NULL,
    published_time_raw VARCHAR(50),
    view_count_raw VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_published_time (published_time),
    INDEX idx_view_count (view_count)
);
```

## Configuration

### Direct Database Connection
```env
USE_SSH_TUNNEL=false
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=youtube_crawler
```

### SSH Tunnel Connection
```env
USE_SSH_TUNNEL=true
SSH_HOST=your_server.com
SSH_USER=your_username
SSH_KEY_PATH=/path/to/key
REMOTE_DB_HOST=127.0.0.1
REMOTE_DB_PORT=3306
LOCAL_BIND_PORT=3307
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=youtube_crawler
```

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick reference guide
- **[DATABASE_GUIDE.md](DATABASE_GUIDE.md)** - Comprehensive documentation
- **[NORMALIZATION_GUIDE.md](NORMALIZATION_GUIDE.md)** - Data normalization details
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Implementation details

## Dependencies

- `requests` - HTTP requests
- `mysql-connector-python` - MySQL driver
- `sshtunnel` - SSH tunnel support
- `python-dotenv` - Environment variables

## Best Practices Implemented

- ✅ Singleton pattern for database manager
- ✅ Repository pattern for data access
- ✅ Connection pooling
- ✅ Context managers
- ✅ Environment-based configuration
- ✅ Comprehensive error handling
- ✅ SQL injection prevention
- ✅ Transaction management
- ✅ Detailed logging

## Security

- Environment variables for credentials
- SSH key authentication support
- Parameterized SQL queries
- `.env` in `.gitignore`
- No hardcoded secrets

## Troubleshooting

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError | `pip install -r requirements.txt` |
| SSH connection failed | Check SSH credentials in `.env` |
| Access denied | Verify database credentials |
| Table doesn't exist | Run `VideoRepository.create_table()` |

## License

MIT License

## Contributing

Contributions are welcome! Please follow the existing code style and best practices.

## Support

For detailed documentation, see:
- [DATABASE_GUIDE.md](DATABASE_GUIDE.md) - Full setup and usage guide
- [QUICKSTART.md](QUICKSTART.md) - Quick reference
- Code comments and docstrings

## Author

YouTube Crawler with Database Integration
