# YouTube Crawler - Database Integration Guide

## Overview

This guide explains how to use the YouTube crawler with MySQL database integration via SSH tunnel. The implementation follows software development best practices including:

- **Singleton Pattern** for database manager
- **Repository Pattern** for data access
- **Connection Pooling** for performance
- **Context Managers** for resource management
- **Proper Error Handling** and logging
- **Environment-based Configuration**
- **Transaction Management**

## Architecture

```
yt-crawler/
├── api/
│   └── videos.py           # Video fetching and normalization
├── database/
│   ├── __init__.py         # Package exports
│   ├── db_manager.py       # Database connection management
│   └── video_repository.py # CRUD operations
├── .env                    # Configuration (create from .env.example)
├── .env.example            # Configuration template
├── requirements.txt        # Dependencies
└── example_with_database.py # Usage example
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `requests` - HTTP requests
- `mysql-connector-python` - MySQL driver
- `sshtunnel` - SSH tunnel support
- `python-dotenv` - Environment variable management

### 2. Configure Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

#### Option A: Direct Database Connection (No SSH Tunnel)

```env
# Database Configuration
USE_SSH_TUNNEL=false
DB_HOST=your_mysql_host
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=youtube_crawler
DB_POOL_SIZE=5
```

#### Option B: SSH Tunnel Connection (Recommended for Remote Servers)

```env
# Enable SSH Tunnel
USE_SSH_TUNNEL=true

# SSH Configuration
SSH_HOST=your_ssh_server.com
SSH_PORT=22
SSH_USER=your_ssh_username

# Choose ONE authentication method:
# Method 1: SSH Key (Recommended)
SSH_KEY_PATH=/path/to/your/private/key

# Method 2: SSH Password (Less secure)
# SSH_PASSWORD=your_ssh_password

# Remote MySQL Server (on SSH server)
REMOTE_DB_HOST=127.0.0.1
REMOTE_DB_PORT=3306

# Local port for tunnel
LOCAL_BIND_PORT=3307

# Database Credentials
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=youtube_crawler
DB_POOL_SIZE=5
```

### 3. Create Database (if needed)

Connect to your MySQL server and create the database:

```sql
CREATE DATABASE youtube_crawler 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
```

The table will be created automatically by the application.

## Usage

### Basic Usage

```python
from api.videos import get_videos
from database import init_database, close_database, VideoRepository

# Initialize database
init_database()

# Create table
VideoRepository.create_table()

# Fetch and save videos
channel_id = 'UCnwxzpFzZNtLH8NgTeAROFA'
videos = get_videos(channel_id, save_to_db=True)

# Close database
close_database()
```

### Run Example Script

```bash
python example_with_database.py
```

### Advanced Usage

#### Fetch Without Saving

```python
from api.videos import get_videos

videos = get_videos(channel_id, save_to_db=False)
```

#### Manual Database Operations

```python
from database import init_database, VideoRepository

init_database()

# Insert single video
video_data = {
    'video_id': 'abc123',
    'published_time': '2024-11-27 19:00:00',
    'view_count': 10000,
    'published_time_raw': '1 day ago',
    'view_count_raw': '10,000 views'
}
VideoRepository.insert_video(video_data)

# Batch insert
VideoRepository.insert_videos_batch(videos)

# Upsert (insert or update)
VideoRepository.upsert_video(video_data)

# Get video
video = VideoRepository.get_video('abc123')

# Get all videos with pagination
videos = VideoRepository.get_all_videos(limit=100, offset=0)

# Get count
count = VideoRepository.get_video_count()

# Delete video
VideoRepository.delete_video('abc123')
```

## Database Schema

```sql
CREATE TABLE videos (
    video_id VARCHAR(20) PRIMARY KEY,
    published_time DATETIME NOT NULL,
    view_count INT UNSIGNED NOT NULL,
    published_time_raw VARCHAR(50),
    view_count_raw VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_published_time (published_time),
    INDEX idx_view_count (view_count),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `video_id` | VARCHAR(20) | YouTube video ID (Primary Key) |
| `published_time` | DATETIME | Normalized publish date |
| `view_count` | INT UNSIGNED | Normalized view count |
| `published_time_raw` | VARCHAR(50) | Original time string (e.g., "1 month ago") |
| `view_count_raw` | VARCHAR(50) | Original view string (e.g., "11,268 views") |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Record last update time |

## Best Practices Implemented

### 1. **Connection Pooling**
- Reuses database connections for better performance
- Configurable pool size via `DB_POOL_SIZE`
- Automatic connection management

### 2. **Context Managers**
```python
# Automatic connection handling
with get_db_cursor() as cursor:
    cursor.execute("SELECT * FROM videos")
    results = cursor.fetchall()
# Connection automatically closed and committed
```

### 3. **Error Handling**
- Graceful handling of duplicate entries
- Transaction rollback on errors
- Detailed logging for debugging

### 4. **Security**
- Environment-based configuration (no hardcoded credentials)
- SSH key authentication support
- Parameterized queries (SQL injection prevention)

### 5. **Singleton Pattern**
- Single database manager instance
- Single SSH tunnel instance
- Prevents resource leaks

### 6. **Repository Pattern**
- Separation of concerns
- Reusable data access methods
- Easy to test and maintain

### 7. **Logging**
- Comprehensive logging throughout
- Different log levels (INFO, WARNING, ERROR)
- Helps with debugging and monitoring

## SSH Tunnel Configuration

### Using SSH Key (Recommended)

1. Generate SSH key pair (if you don't have one):
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/yt_crawler_key
```

2. Copy public key to server:
```bash
ssh-copy-id -i ~/.ssh/yt_crawler_key.pub user@your_server.com
```

3. Set in `.env`:
```env
SSH_KEY_PATH=/home/user/.ssh/yt_crawler_key
```

### Using SSH Password

Set in `.env`:
```env
SSH_PASSWORD=your_password
```

**Note:** SSH key authentication is more secure and recommended for production.

## Troubleshooting

### Connection Issues

1. **SSH Tunnel Fails**
   - Verify SSH credentials
   - Check firewall rules
   - Ensure SSH server allows port forwarding

2. **Database Connection Fails**
   - Verify database credentials
   - Check MySQL is running
   - Verify database exists

3. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python path

### Common Errors

**Error:** `ModuleNotFoundError: No module named 'database'`
- **Solution:** Run from project root directory

**Error:** `Access denied for user`
- **Solution:** Verify database credentials in `.env`

**Error:** `SSH tunnel connection failed`
- **Solution:** Check SSH credentials and server accessibility

## Performance Considerations

1. **Connection Pool Size**
   - Default: 5 connections
   - Increase for high concurrency: `DB_POOL_SIZE=10`

2. **Batch Operations**
   - Use `upsert_videos_batch()` for multiple videos
   - More efficient than individual inserts

3. **Indexes**
   - Indexes on `published_time` and `view_count` for fast queries
   - Consider adding more indexes based on query patterns

## Security Checklist

- [ ] `.env` file added to `.gitignore`
- [ ] Using SSH key authentication (not password)
- [ ] Database user has minimal required permissions
- [ ] SSL/TLS enabled for database connection (if available)
- [ ] Regular security updates for dependencies

## Example Queries

### Get most viewed videos
```python
with get_db_cursor() as cursor:
    cursor.execute("""
        SELECT video_id, view_count, published_time 
        FROM videos 
        ORDER BY view_count DESC 
        LIMIT 10
    """)
    top_videos = cursor.fetchall()
```

### Get recent videos
```python
with get_db_cursor() as cursor:
    cursor.execute("""
        SELECT video_id, published_time, view_count 
        FROM videos 
        WHERE published_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        ORDER BY published_time DESC
    """)
    recent_videos = cursor.fetchall()
```

### Get average views
```python
with get_db_cursor() as cursor:
    cursor.execute("SELECT AVG(view_count) as avg_views FROM videos")
    result = cursor.fetchone()
    avg_views = result['avg_views']
```

## License

This project follows best practices for production-ready database integration.

## Support

For issues or questions, please check:
1. This documentation
2. Error logs
3. Environment configuration
