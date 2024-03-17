import undetected_chromedriver as uc
import json
import time
import sqlite3
import random
from tqdm import tqdm

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

def queue_list():
    # Execute the SQL query
    query = f"""
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
        """
    cursor.execute(query)
    # Fetch the results
    channelIds = cursor.fetchall()
    channelIds=[i[0] for i in channelIds]
    print(f'Total : {len(channelIds)} channels to crawl')
    return channelIds

def parse_logs():
    SEARCH_API = 'https://www.youtube.com/youtubei/v1/browse'
    logs = driver.get_log("performance")
    logs = [json.loads(lr["message"])["message"] for lr in logs]
    for log in logs:
        try:
            resp_url = log["params"]["response"]["url"]
            if SEARCH_API in resp_url:
                request_id = log["params"]["requestId"]
                response_body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
                response_json = json.loads(response_body['body'])
                return response_json
        except Exception as e:
            pass
    return None

def save_data(channelId,videos):
    for each_video_item in videos:
        sqlite_insert_with_param = """INSERT OR IGNORE INTO youtube_videos
                                        (channelId,videoId,data) 
                                        VALUES (?,?,?);"""
        videoId=each_video_item['videoId']
        data_tuple = (channelId,videoId,json.dumps(each_video_item, ensure_ascii=False).encode('utf8'))
        cursor.execute(sqlite_insert_with_param, data_tuple)
        conn.commit()
        print(f'Crawled - channelId : {channelId}, videoId : {videoId}')

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--mute-audio")
    caps = options.to_capabilities()
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}
    driver = uc.Chrome(
        headless=True,
        options=options,
        desired_capabilities=caps,
        use_subprocess=True
    )
    return driver

channelId_queue=queue_list()
driver=get_driver()
counter=0
for channelId in tqdm(channelId_queue):
    counter+=1
    if counter%100==0:
        driver.close()
        driver.quit()
        driver=get_driver()
        print('Restarted browser.....')
    driver.get(f'https://www.youtube.com/channel/{channelId}/videos')
    time.sleep(random.uniform(2,4))
    a=driver.get_log("performance")
    if "This account has been terminated" not in driver.page_source:
        try:
            driver.find_element('xpath','//yt-formatted-string[text()="Oldest"]').click()
            time.sleep(random.uniform(2,4))
            response_json=parse_logs()
            videos=response_json['onResponseReceivedActions'][1]['reloadContinuationItemsCommand']['continuationItems']
            videos=[i['richItemRenderer']['content']['videoRenderer'] for i in videos if 'richItemRenderer' in i.keys()]
        except:
            videos=[{'videoId':'Need to recheck, no Oldest button'}]
    else:
        videos=[{'videoId':'This account has been terminated'}]
    save_data(channelId,videos)

driver.close()
driver.quit()
