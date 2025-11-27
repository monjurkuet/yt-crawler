# Data Normalization for MySQL

## Summary

The `api/videos.py` file has been updated to normalize YouTube video data for MySQL storage:

### 1. View Count Normalization

**Function:** `normalize_view_count(view_count_str)`

**Input Examples:**
- "11,268 views"
- "1.2M views"
- "5.3K views"

**Output:** Integer (e.g., 11268, 1200000, 5300)

**MySQL Data Type:** 
- `INT` - For view counts up to 2,147,483,647 (sufficient for most videos)
- `BIGINT` - For extremely popular videos with > 2.1B views

**Recommended:** `INT UNSIGNED` (range: 0 to 4,294,967,295)

```sql
CREATE TABLE videos (
    video_id VARCHAR(20) PRIMARY KEY,
    view_count INT UNSIGNED,
    ...
);
```

### 2. Published Time Normalization

**Function:** `normalize_published_time(published_time_str, reference_time=None)`

**Input Examples:**
- "1 month ago"
- "2 days ago"
- "3 weeks ago"

**Output:** MySQL DATETIME format string (e.g., "2025-10-28 19:15:51")

**MySQL Data Type:** `DATETIME`

**Recommended:** `DATETIME` (range: '1000-01-01 00:00:00' to '9999-12-31 23:59:59')

```sql
CREATE TABLE videos (
    video_id VARCHAR(20) PRIMARY KEY,
    published_time DATETIME,
    ...
);
```

**Alternative:** `TIMESTAMP` if you need automatic timezone conversion (range: '1970-01-01 00:00:01' UTC to '2038-01-19 03:14:07' UTC)

### 3. Complete MySQL Table Schema

```sql
CREATE TABLE videos (
    video_id VARCHAR(20) PRIMARY KEY,
    published_time DATETIME NOT NULL,
    view_count INT UNSIGNED NOT NULL,
    published_time_raw VARCHAR(50),  -- Optional: keep original data
    view_count_raw VARCHAR(50),      -- Optional: keep original data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_published_time (published_time),
    INDEX idx_view_count (view_count)
);
```

### 4. Features

- **Handles multiple formats:** Supports K, M, B abbreviations for view counts
- **Relative time conversion:** Converts seconds, minutes, hours, days, weeks, months, and years
- **Null safety:** Returns `None` for invalid or missing data
- **Raw data preservation:** Optionally keeps original strings for debugging
- **MySQL-ready:** Output formats are directly compatible with MySQL

### 5. Usage Example

```python
from api.videos import get_videos

videos = get_videos('UCnwxzpFzZNtLH8NgTeAROFA')

# Output format:
# {
#     "video_id": "mmE5J91w-uQ",
#     "published_time": "2025-10-28 19:15:51",  # DATETIME format
#     "view_count": 11268,                       # Integer
#     "published_time_raw": "1 month ago",       # Original
#     "view_count_raw": "11,268 views"           # Original
# }
```

### 6. Notes

- **Month approximation:** 1 month = 30 days (approximate)
- **Year approximation:** 1 year = 365 days (approximate)
- **Timezone:** Uses local system time by default
- **Precision:** Time calculations are approximate for relative dates
