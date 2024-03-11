SELECT 
json_extract(data, '$.aboutChannelViewModel.canonicalChannelUrl') AS canonicalChannelUrl,
  json_extract(data, '$.aboutChannelViewModel.joinedDateText.content') AS joinedDate,
  json_extract(data, '$.aboutChannelViewModel.country') AS country,
  json_extract(data, '$.aboutChannelViewModel.subscriberCountText') AS subscriberCountText,
  json_extract(data, '$.aboutChannelViewModel.viewCountText') AS viewCountText,
  json_extract(data, '$.aboutChannelViewModel.videoCountText') AS videoCountText,
  json_extract(data, '$.aboutChannelViewModel.description') AS description
FROM channel_details
WHERE joinedDate like '%2023%' and country like '%united states%'
;
