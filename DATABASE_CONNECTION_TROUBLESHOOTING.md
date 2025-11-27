# Database Connection Troubleshooting

## Error: Can't connect to MySQL server on 'localhost:3306'

This error means the application can't connect to MySQL. Here are the solutions:

---

## Solution 1: Using SSH Tunnel (Recommended for Remote Database)

If your MySQL database is on a remote server, configure SSH tunnel:

### Step 1: Edit your `.env` file

```env
# Application Configuration
SAVE_TO_DB=true

# Enable SSH Tunnel
USE_SSH_TUNNEL=true

# SSH Configuration
SSH_HOST=your_remote_server.com
SSH_PORT=22
SSH_USER=your_ssh_username
SSH_KEY_PATH=C:/Users/YourName/.ssh/id_rsa
# OR use password (less secure):
# SSH_PASSWORD=your_ssh_password

# Remote MySQL Configuration (on the SSH server)
REMOTE_DB_HOST=127.0.0.1
REMOTE_DB_PORT=3306

# Local tunnel port
LOCAL_BIND_PORT=3307

# Database Credentials
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=youtube_crawler
DB_POOL_SIZE=5
```

### Step 2: Test SSH Connection

Before running the app, test your SSH connection:

```bash
ssh your_ssh_username@your_remote_server.com
```

If this works, the SSH tunnel should work too.

---

## Solution 2: Using Local MySQL Server

If you have MySQL installed locally:

### Step 1: Start MySQL Server

**Windows:**
```bash
# Start MySQL service
net start MySQL80
# or
net start MySQL
```

**Check if MySQL is running:**
```bash
# Try to connect
mysql -u root -p
```

### Step 2: Edit your `.env` file

```env
# Application Configuration
SAVE_TO_DB=true

# Disable SSH Tunnel
USE_SSH_TUNNEL=false

# Direct Database Connection
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=youtube_crawler
DB_POOL_SIZE=5
```

### Step 3: Create Database

```sql
CREATE DATABASE youtube_crawler 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
```

---

## Solution 3: Disable Database Saving (Quick Test)

If you just want to test video fetching without database:

### Edit `.env`:
```env
SAVE_TO_DB=false
```

Then run:
```bash
python api/videos.py
```

This will fetch videos without trying to save to database.

---

## Verification Steps

### 1. Check MySQL is Running

**Windows:**
```bash
# Check if MySQL service is running
sc query MySQL80
# or
sc query MySQL
```

**Test connection:**
```bash
mysql -h localhost -P 3306 -u your_username -p
```

### 2. Check SSH Connection (if using tunnel)

```bash
ssh -v your_username@your_server.com
```

### 3. Test Port Availability

**Check if port 3306 is open:**
```bash
# Windows PowerShell
Test-NetConnection -ComputerName localhost -Port 3306
```

---

## Common Issues and Solutions

### Issue 1: MySQL Not Installed

**Solution:** Install MySQL
- Download from: https://dev.mysql.com/downloads/mysql/
- Or use XAMPP/WAMP which includes MySQL

### Issue 2: MySQL Service Not Running

**Solution:** Start the service
```bash
# Windows
net start MySQL80

# Or use Services app (services.msc)
# Find "MySQL80" and click Start
```

### Issue 3: Wrong Credentials

**Solution:** Verify credentials
```bash
# Test connection
mysql -u your_username -p
# Enter password when prompted
```

### Issue 4: Firewall Blocking Connection

**Solution:** Check firewall
- Allow port 3306 in Windows Firewall
- Or temporarily disable firewall to test

### Issue 5: SSH Key Not Found

**Solution:** Generate SSH key
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
# Copy public key to server
ssh-copy-id user@server.com
```

---

## Quick Configuration Examples

### Example 1: Local MySQL (No SSH)
```env
SAVE_TO_DB=true
USE_SSH_TUNNEL=false
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=mypassword
DB_NAME=youtube_crawler
```

### Example 2: Remote MySQL via SSH (Password)
```env
SAVE_TO_DB=true
USE_SSH_TUNNEL=true
SSH_HOST=myserver.com
SSH_PORT=22
SSH_USER=ubuntu
SSH_PASSWORD=mysshpassword
REMOTE_DB_HOST=127.0.0.1
REMOTE_DB_PORT=3306
LOCAL_BIND_PORT=3307
DB_USER=dbuser
DB_PASSWORD=dbpassword
DB_NAME=youtube_crawler
```

### Example 3: Remote MySQL via SSH (Key)
```env
SAVE_TO_DB=true
USE_SSH_TUNNEL=true
SSH_HOST=myserver.com
SSH_PORT=22
SSH_USER=ubuntu
SSH_KEY_PATH=/home/user/.ssh/id_rsa
REMOTE_DB_HOST=127.0.0.1
REMOTE_DB_PORT=3306
LOCAL_BIND_PORT=3307
DB_USER=dbuser
DB_PASSWORD=dbpassword
DB_NAME=youtube_crawler
```

### Example 4: No Database (Testing Only)
```env
SAVE_TO_DB=false
```

---

## Next Steps

1. **Decide which solution fits your setup:**
   - Have local MySQL? → Use Solution 2
   - Have remote MySQL? → Use Solution 1
   - Just testing? → Use Solution 3

2. **Edit your `.env` file** with the appropriate configuration

3. **Test the connection:**
   ```bash
   python example_with_database.py
   ```

4. **If still having issues:**
   - Check the error message carefully
   - Verify MySQL is running
   - Verify credentials are correct
   - Check firewall settings

---

## Getting Help

If you're still stuck, provide:
1. Where is your MySQL database? (local or remote)
2. Can you connect to MySQL directly? (using mysql command)
3. Are you using SSH tunnel?
4. What's in your `.env` file? (without passwords)

---

## Summary

✅ **Local MySQL** → Set `USE_SSH_TUNNEL=false`, start MySQL service
✅ **Remote MySQL** → Set `USE_SSH_TUNNEL=true`, configure SSH details
✅ **No Database** → Set `SAVE_TO_DB=false` for testing
✅ **Test First** → Always test MySQL/SSH connection before running app
