SELECT *,
       SUBSTR(json_extract(data, '$.videoCountText.simpleText'), 1, INSTR(json_extract(data, '$.videoCountText.simpleText'), ' ') - 1) AS SubscribersCount,
       CASE
         WHEN SUBSTR(json_extract(data, '$.videoCountText.simpleText'), 1, INSTR(json_extract(data, '$.videoCountText.simpleText'), ' ') - 1) like '%k%' THEN
           CAST(REPLACE(SUBSTR(json_extract(data, '$.videoCountText.simpleText'), 1, LENGTH(json_extract(data, '$.videoCountText.simpleText')) - 1), ',', '') AS REAL) * 1000
         ELSE
           CAST(REPLACE(SUBSTR(json_extract(data, '$.videoCountText.simpleText'), 1, INSTR(json_extract(data, '$.videoCountText.simpleText'), ' ') - 1), ',', '') AS REAL)
       END AS numeric_SubscribersCount
	   
FROM channels
WHERE SubscribersCount NOT LIKE '%M%' and numeric_SubscribersCount>=2500
and channelId not in (Select channelId from channel_details);
