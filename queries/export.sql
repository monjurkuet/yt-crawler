SELECT *, MIN(timestamp),max(timestamp) FROM youtube_videos 
LEFT JOIN timedata on
youtube_videos.videoId=timedata.videoId
LEFT JOIN channel_details_parsed on
youtube_videos.channelId=channel_details_parsed.channelId
GROUP by youtube_videos.channelId