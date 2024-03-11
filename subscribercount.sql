SELECT *,
       SUBSTR(json_extract(data, '$.videoCountText.simpleText'), 1, INSTR(json_extract(data, '$.videoCountText.simpleText'), ' ') - 1) AS videoCount,
       CASE
         WHEN SUBSTR(json_extract(data, '$.videoCountText.simpleText'), 1, INSTR(json_extract(data, '$.videoCountText.simpleText'), ' ') - 1) like '%k%' THEN
           CAST(REPLACE(SUBSTR(json_extract(data, '$.videoCountText.simpleText'), 1, LENGTH(json_extract(data, '$.videoCountText.simpleText')) - 1), ',', '') AS REAL) * 1000
         ELSE
           CAST(REPLACE(SUBSTR(json_extract(data, '$.videoCountText.simpleText'), 1, INSTR(json_extract(data, '$.videoCountText.simpleText'), ' ') - 1), ',', '') AS REAL)
       END AS numeric_videoCount
FROM channels
WHERE videoCount NOT LIKE '%M%' and numeric_videoCount>=20001 and numeric_videoCount<=40000 and channels.channelId not in (SELECT channelId from channel_details);
