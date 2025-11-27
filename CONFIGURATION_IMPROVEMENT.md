# Configuration Improvement - SAVE_TO_DB Environment Variable

## What Changed?

The `save_to_db` parameter is now **environment-based** instead of requiring explicit parameter passing. This follows the **12-Factor App** methodology and makes configuration more flexible.

## Before (Parameter-based)

```python
# Had to explicitly pass save_to_db every time
videos = get_videos(channel_id, save_to_db=True)
```

## After (Environment-based)

```python
# Reads from .env automatically
videos = get_videos(channel_id)  # Uses SAVE_TO_DB from .env

# Can still override if needed
videos = get_videos(channel_id, save_to_db=False)  # Override to disable
```

## Configuration in .env

```env
# Application Configuration
SAVE_TO_DB=true  # Set to 'false' to disable database saving
```

## Benefits

### 1. **Configuration Over Code**
- Change behavior without modifying code
- Different settings for dev/staging/production
- No code changes needed to enable/disable database saving

### 2. **Environment-Specific Behavior**
```bash
# Development - no database
SAVE_TO_DB=false

# Production - save to database
SAVE_TO_DB=true
```

### 3. **Backward Compatible**
```python
# Still works - uses env var
videos = get_videos(channel_id)

# Still works - explicit override
videos = get_videos(channel_id, save_to_db=True)
videos = get_videos(channel_id, save_to_db=False)
```

### 4. **Cleaner Code**
```python
# Before - repetitive
videos1 = get_videos(channel1, save_to_db=True)
videos2 = get_videos(channel2, save_to_db=True)
videos3 = get_videos(channel3, save_to_db=True)

# After - clean
videos1 = get_videos(channel1)
videos2 = get_videos(channel2)
videos3 = get_videos(channel3)
```

## Implementation Details

### In `api/videos.py`

```python
def get_videos(channel_id, save_to_db=None):
    """
    Fetch videos from a YouTube channel
    
    Args:
        channel_id: YouTube channel ID
        save_to_db: If True, save videos to database. 
                   If None, uses SAVE_TO_DB env var (default)
    """
    # Use environment variable if save_to_db not explicitly set
    if save_to_db is None:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        save_to_db = os.getenv('SAVE_TO_DB', 'false').lower() == 'true'
    
    # Rest of the function...
```

### Priority Order

1. **Explicit parameter** (if provided) - Highest priority
2. **Environment variable** (if parameter is None)
3. **Default value** (`false` if env var not set)

## Usage Examples

### Example 1: Use Environment Configuration
```python
# .env: SAVE_TO_DB=true
videos = get_videos('CHANNEL_ID')  # Saves to database
```

### Example 2: Override Environment
```python
# .env: SAVE_TO_DB=true
videos = get_videos('CHANNEL_ID', save_to_db=False)  # Does NOT save
```

### Example 3: Development vs Production
```python
# Same code works in both environments

# Development .env:
# SAVE_TO_DB=false
# USE_SSH_TUNNEL=false

# Production .env:
# SAVE_TO_DB=true
# USE_SSH_TUNNEL=true

# Code (same in both):
videos = get_videos('CHANNEL_ID')  # Behavior depends on environment
```

## Migration Guide

### If you have existing code:

**Old code:**
```python
videos = get_videos(channel_id, save_to_db=True)
```

**Option 1: Use environment variable (recommended)**
```python
# Set in .env: SAVE_TO_DB=true
videos = get_videos(channel_id)
```

**Option 2: Keep explicit parameter (still works)**
```python
# No changes needed
videos = get_videos(channel_id, save_to_db=True)
```

## Best Practices

### 1. Set in .env for Application-Wide Behavior
```env
# .env
SAVE_TO_DB=true
```

### 2. Override Only When Needed
```python
# Normal operation - uses env var
videos = get_videos(channel_id)

# Special case - override
test_videos = get_videos(test_channel, save_to_db=False)
```

### 3. Different Environments
```bash
# .env.development
SAVE_TO_DB=false
USE_SSH_TUNNEL=false

# .env.production
SAVE_TO_DB=true
USE_SSH_TUNNEL=true
```

## Updated .env.example

```env
# Application Configuration
SAVE_TO_DB=true

# Database Configuration
USE_SSH_TUNNEL=false
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=youtube_crawler
DB_POOL_SIZE=5

# SSH Tunnel Configuration
SSH_HOST=your_ssh_host
SSH_PORT=22
SSH_USER=your_ssh_username
SSH_KEY_PATH=/path/to/your/private/key

# MySQL server details (on remote server)
REMOTE_DB_HOST=127.0.0.1
REMOTE_DB_PORT=3306

# Local port for SSH tunnel
LOCAL_BIND_PORT=3307
```

## Summary

This improvement makes the application more configurable and follows industry best practices:

✅ **12-Factor App** - Configuration in environment
✅ **Flexibility** - Different settings per environment
✅ **Cleaner Code** - Less repetition
✅ **Backward Compatible** - Existing code still works
✅ **Override Capability** - Can still override when needed

## Credits

Suggested by user - great improvement! 🎉
