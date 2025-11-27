# Running from Different Directories

## Issue Fixed

Previously, running `python videos.py` from the `api/` directory would fail with:
```
Error saving to database: No module named 'database'
```

## Solution

Added path manipulation to `api/videos.py`:

```python
import sys
import os

# Add parent directory to path to allow imports from any location
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

## Now You Can Run From Anywhere

### From project root:
```bash
cd D:\githubrepose\yt-crawler
python api/videos.py
```

### From api directory:
```bash
cd D:\githubrepose\yt-crawler\api
python videos.py
```

### From anywhere with full path:
```bash
python D:\githubrepose\yt-crawler\api\videos.py
```

## Database Initialization Note

If you see this error:
```
Error saving to database: 'NoneType' object has no attribute 'get_connection'
```

It means `SAVE_TO_DB=true` in your `.env` but the database wasn't initialized. This is expected behavior when running `videos.py` directly.

### To use database, run the example script instead:
```bash
python example_with_database.py
```

Or initialize the database in your code:
```python
from database import init_database, close_database
from api.videos import get_videos

init_database()
videos = get_videos('CHANNEL_ID')
close_database()
```

## Quick Test (No Database)

To test video fetching without database:

1. **Set in .env:**
   ```env
   SAVE_TO_DB=false
   ```

2. **Run from any directory:**
   ```bash
   python api/videos.py
   ```

3. **Or override in code:**
   ```python
   videos = get_videos('CHANNEL_ID', save_to_db=False)
   ```

## Summary

✅ **Fixed** - Can now run from any directory
✅ **Flexible** - Works with or without database
✅ **Clean** - Proper error handling
✅ **User-friendly** - Clear error messages
