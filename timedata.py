import sqlite3
from datetime import datetime, timedelta

# Connect to the SQLite database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Function to convert string to timedelta
def parse_timedelta(s):
    if 'year' in s:
        n = int(s.split()[0])
        return timedelta(days=n*365)
    elif 'month' in s:
        n = int(s.split()[0])
        return timedelta(days=n*30)
    elif 'week' in s:
        n = int(s.split()[0])
        return timedelta(weeks=n)
    elif 'day' in s:
        n = int(s.split()[0])
        return timedelta(days=n)
    elif 'hour' in s:
        n = int(s.split()[0])
        return timedelta(hours=n)
    elif 'minute' in s:
        n = int(s.split()[0])
        return timedelta(minutes=n)
    else:
        return timedelta(0)

# Fetch all rows from the table
cursor.execute("SELECT videoId,json_extract(data, '$.publishedTimeText.simpleText') AS publishedTime,updatedAt FROM youtube_videos where videoId not in (select videoId from timedata) and publishedTime is not NULL")
rows = cursor.fetchall()

# Convert each row to a timestamp relative to the present time
for row in rows:
    videoId=row[0]
    publishedTime = row[1]
    updatedAt=datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
    time_diff = parse_timedelta(publishedTime)
    timestamp = updatedAt - time_diff
    print("Original:", publishedTime, "Timestamp:", timestamp)
    # Insert the converted timestamp into the new table
    cursor.execute("INSERT OR IGNORE INTO timedata (videoId, timestamp) VALUES (?, ?)", (videoId, timestamp))
    # Commit changes to the database
    conn.commit()

# Close the connection
conn.close()
