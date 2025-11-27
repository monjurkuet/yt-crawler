# Quick Start Guide - Database Integration

## 1. Install Dependencies
```bash
pip install -r requirements.txt
```

## 2. Configure Environment
```bash
# Copy template
cp .env.example .env

# Edit .env with your credentials
# Set USE_SSH_TUNNEL=true if using SSH tunnel
```

## 3. Run Example
```bash
python example_with_database.py
```

## Quick Code Examples

### Fetch and Save Videos
```python
from api.videos import get_videos
from database import init_database, close_database

init_database()
# Saves to DB if SAVE_TO_DB=true in .env
videos = get_videos('CHANNEL_ID')
close_database()
```

### Override Environment Setting
```python
# Force save regardless of .env setting
videos = get_videos('CHANNEL_ID', save_to_db=True)

# Force no save regardless of .env setting
videos = get_videos('CHANNEL_ID', save_to_db=False)
```

### Manual Database Operations
```python
from database import VideoRepository, init_database

init_database()

# Create table
VideoRepository.create_table()

# Insert videos
VideoRepository.upsert_videos_batch(videos)

# Query videos
all_videos = VideoRepository.get_all_videos(limit=10)
video = VideoRepository.get_video('VIDEO_ID')
count = VideoRepository.get_video_count()
```

## Configuration Options

### Direct Connection
```env
SAVE_TO_DB=true
USE_SSH_TUNNEL=false
DB_HOST=localhost
DB_PORT=3306
DB_USER=username
DB_PASSWORD=password
DB_NAME=youtube_crawler
```

### SSH Tunnel
```env
SAVE_TO_DB=true
USE_SSH_TUNNEL=true
SSH_HOST=server.com
SSH_USER=username
SSH_KEY_PATH=/path/to/key
REMOTE_DB_HOST=127.0.0.1
REMOTE_DB_PORT=3306
LOCAL_BIND_PORT=3307
DB_USER=username
DB_PASSWORD=password
DB_NAME=youtube_crawler
```

## Common Commands

```bash
# Test database connection
python -c "from database import init_database; init_database(); print('✓ Connected')"

# Create table
python -c "from database import init_database, VideoRepository; init_database(); VideoRepository.create_table(); print('✓ Table created')"

# Check video count
python -c "from database import init_database, VideoRepository; init_database(); print(f'Videos: {VideoRepository.get_video_count()}')"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError | `pip install -r requirements.txt` |
| SSH connection failed | Check SSH credentials in `.env` |
| Access denied | Verify database credentials |
| Table doesn't exist | Run `VideoRepository.create_table()` |

## Files Created

- `database/db_manager.py` - Connection management
- `database/video_repository.py` - CRUD operations
- `database/__init__.py` - Package exports
- `.env.example` - Configuration template
- `requirements.txt` - Dependencies
- `example_with_database.py` - Usage example
- `DATABASE_GUIDE.md` - Full documentation

## Next Steps

1. Configure `.env` with your credentials
2. Run `example_with_database.py` to test
3. Read `DATABASE_GUIDE.md` for detailed documentation
4. Integrate into your workflow
