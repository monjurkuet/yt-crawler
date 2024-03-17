SELECT 
  channelId,
  json_extract(data, '$.aboutChannelViewModel.canonicalChannelUrl') AS canonicalChannelUrl,
  json_extract(data, '$.aboutChannelViewModel.joinedDateText.content') AS joinedDate,
  json_extract(data, '$.aboutChannelViewModel.country') AS country,
  json_extract(data, '$.aboutChannelViewModel.subscriberCountText') AS subscriberCountText,
  json_extract(data, '$.aboutChannelViewModel.viewCountText') AS viewCountText,
  CAST(REPLACE(substr(json_extract(data, '$.aboutChannelViewModel.viewCountText'), 1, instr(json_extract(data, '$.aboutChannelViewModel.viewCountText'), ' ') - 1), ',', '') AS INTEGER) AS viewCount,
  json_extract(data, '$.aboutChannelViewModel.videoCountText') AS videoCountText,
  CAST(REPLACE(substr(json_extract(data, '$.aboutChannelViewModel.videoCountText'), 1, instr(json_extract(data, '$.aboutChannelViewModel.videoCountText'), ' ') - 1), ',', '') AS INTEGER) AS videoCount,
  json_extract(data, '$.aboutChannelViewModel.description') AS description
FROM channel_details
	WHERE 
		canonicalChannelUrl is not NULL
		and videoCount<101
		and videoCount>=10
		and viewCount>50000
		and channelId not in (SELECT DISTINCT channelId from youtube_videos)