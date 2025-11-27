# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        YouTube Crawler                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐         ┌──────────────────┐            │
│  │  api/videos.py   │────────▶│  Normalization   │            │
│  │                  │         │  Functions       │            │
│  │ - get_videos()   │         │ - normalize_*()  │            │
│  └──────────────────┘         └──────────────────┘            │
│           │                                                     │
│           │ save_to_db=True                                    │
│           ▼                                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     Data Access Layer                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          database/video_repository.py                    │  │
│  │                                                          │  │
│  │  - create_table()                                       │  │
│  │  - insert_video()                                       │  │
│  │  - insert_videos_batch()                                │  │
│  │  - upsert_video()                                       │  │
│  │  - upsert_videos_batch()                                │  │
│  │  - get_video()                                          │  │
│  │  - get_all_videos()                                     │  │
│  │  - delete_video()                                       │  │
│  │  - get_video_count()                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                     │
│                           │ Uses                                │
│                           ▼                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  Database Management Layer                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          database/db_manager.py                          │  │
│  │                                                          │  │
│  │  DatabaseManager (Singleton)                            │  │
│  │  ├─ SSH Tunnel Management                               │  │
│  │  ├─ Connection Pool                                     │  │
│  │  ├─ Context Managers                                    │  │
│  │  └─ Error Handling                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                     │
│                           │                                     │
│                           ▼                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐         ┌──────────────────┐            │
│  │   SSH Tunnel     │────────▶│   MySQL Server   │            │
│  │   (Optional)     │         │                  │            │
│  │                  │         │  ┌────────────┐  │            │
│  │  Local: 3307     │         │  │   videos   │  │            │
│  │  Remote: 3306    │         │  │   table    │  │            │
│  └──────────────────┘         │  └────────────┘  │            │
│                               └──────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
1. Fetch Videos
   ┌─────────────┐
   │ YouTube API │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ api/videos  │
   │ .get_videos │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ Normalize   │
   │ Data        │
   └──────┬──────┘
          │
          ▼

2. Save to Database (if save_to_db=True)
   ┌─────────────────┐
   │ VideoRepository │
   │ .upsert_batch   │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ DatabaseManager │
   │ .get_cursor()   │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ Connection Pool │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ SSH Tunnel      │
   │ (if enabled)    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ MySQL Database  │
   └─────────────────┘
```

## Component Responsibilities

### api/videos.py
- Fetch video data from YouTube
- Normalize data for database
- Optionally save to database
- Handle API errors

### database/video_repository.py
- CRUD operations for videos
- Batch operations
- Upsert functionality
- Query methods
- Business logic for data access

### database/db_manager.py
- Manage database connections
- SSH tunnel management
- Connection pooling
- Resource cleanup
- Error handling
- Logging

## Design Patterns Used

### 1. Singleton Pattern
```python
class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```
**Purpose:** Ensure single database manager and SSH tunnel instance

### 2. Repository Pattern
```python
class VideoRepository:
    @staticmethod
    def insert_video(video_data):
        # Data access logic
```
**Purpose:** Separate data access from business logic

### 3. Context Manager Pattern
```python
with get_db_cursor() as cursor:
    cursor.execute("SELECT * FROM videos")
    # Automatic commit and cleanup
```
**Purpose:** Automatic resource management

### 4. Factory Pattern
```python
def init_database():
    db_manager.initialize()
```
**Purpose:** Centralized initialization

## Configuration Flow

```
.env file
    │
    ▼
Environment Variables
    │
    ▼
DatabaseManager.__init__()
    │
    ├─▶ SSH Configuration
    │   ├─ SSH_HOST
    │   ├─ SSH_USER
    │   └─ SSH_KEY_PATH
    │
    └─▶ Database Configuration
        ├─ DB_HOST
        ├─ DB_PORT
        ├─ DB_USER
        ├─ DB_PASSWORD
        └─ DB_NAME
```

## Error Handling Strategy

```
Try-Catch Hierarchy:

Application Level (api/videos.py)
    │
    ├─▶ Continue on database errors
    │   (fetch still succeeds)
    │
    └─▶ Return empty list on fetch errors

Repository Level (video_repository.py)
    │
    ├─▶ Log duplicate key errors
    │   (skip duplicates)
    │
    ├─▶ Rollback on transaction errors
    │
    └─▶ Raise critical errors

Manager Level (db_manager.py)
    │
    ├─▶ Rollback transactions
    │
    ├─▶ Close connections
    │
    └─▶ Cleanup resources
```

## Security Layers

```
1. Environment Variables
   └─▶ No hardcoded credentials

2. SSH Tunnel
   └─▶ Encrypted connection

3. SSH Key Authentication
   └─▶ More secure than passwords

4. Parameterized Queries
   └─▶ SQL injection prevention

5. .gitignore
   └─▶ Prevent credential leaks

6. Connection Pooling
   └─▶ Resource limits
```

## Performance Optimizations

### 1. Connection Pooling
- Reuse connections
- Configurable pool size
- Reduced connection overhead

### 2. Batch Operations
- Insert multiple videos in one transaction
- Reduced network round trips
- Better throughput

### 3. Indexes
- `idx_published_time` - Fast date queries
- `idx_view_count` - Fast view count queries
- `idx_created_at` - Fast recent data queries

### 4. Upsert Operations
- Single query for insert or update
- Reduced database calls
- Atomic operations

## Scalability Considerations

```
Current Setup (Single Server)
    │
    ├─▶ Connection Pool (5 connections)
    ├─▶ Single MySQL instance
    └─▶ SSH tunnel

Future Scaling Options:
    │
    ├─▶ Increase pool size (10-20)
    ├─▶ Read replicas
    ├─▶ Caching layer (Redis)
    ├─▶ Horizontal partitioning
    └─▶ Load balancer
```

## Monitoring Points

1. **Connection Pool**
   - Active connections
   - Pool exhaustion

2. **Query Performance**
   - Slow query log
   - Query execution time

3. **SSH Tunnel**
   - Tunnel status
   - Connection drops

4. **Error Rates**
   - Database errors
   - API errors
   - Duplicate entries

5. **Data Quality**
   - Null values
   - Normalization failures
   - Data consistency
```
