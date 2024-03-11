import undetected_chromedriver as uc
import json
import time
import sqlite3
import random
from tqdm import tqdm

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

def queue_list(start_sub,end_sub):
    # Execute the SQL query
    query = f"""
    SELECT *,
       SUBSTR(json_extract(data, '$.videoCountText.simpleText'), 1, INSTR(json_extract(data, '$.videoCountText.simpleText'), ' ') - 1) AS subsCount,
       CASE
         WHEN SUBSTR(json_extract(data, '$.videoCountText.simpleText'), 1, INSTR(json_extract(data, '$.videoCountText.simpleText'), ' ') - 1) like '%k%' THEN
           CAST(REPLACE(SUBSTR(json_extract(data, '$.videoCountText.simpleText'), 1, LENGTH(json_extract(data, '$.videoCountText.simpleText')) - 1), ',', '') AS REAL) * 1000
         ELSE
           CAST(REPLACE(SUBSTR(json_extract(data, '$.videoCountText.simpleText'), 1, INSTR(json_extract(data, '$.videoCountText.simpleText'), ' ') - 1), ',', '') AS REAL)
       END AS numeric_subsCount
    FROM channels
    WHERE subsCount NOT LIKE '%M%' and numeric_subsCount>={start_sub} and numeric_subsCount<={end_sub} and channels.channelId not in (SELECT channelId from channel_details);
    """
    cursor.execute(query)
    # Fetch the results
    results = cursor.fetchall()
    results=[i[0] for i in results]
    return results

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

def save_data(channelId,about_data):
    sqlite_insert_with_param = """INSERT OR IGNORE INTO channel_details
                                    (channelId,data) 
                                    VALUES (?,?);"""
    data_tuple = (channelId,json.dumps(about_data, ensure_ascii=False).encode('utf8'))
    cursor.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()
    print('Crawled : ',channelId)

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
start_sub=input('start_sub')
end_sub=input('end_sub')
channelId_queue=queue_list(start_sub,end_sub)
driver=get_driver()
counter=0
for channelId in tqdm(channelId_queue):
    counter+=1
    if counter%100==0:
        driver.close()
        driver.quit()
        driver=get_driver()
    driver.get(f'https://www.youtube.com/channel/{channelId}')
    time.sleep(random.uniform(2,4))
    if "This account has been terminated" not in driver.page_source:
        try:
            driver.find_element('xpath','//yt-icon[@id="more-icon"]').click()
            time.sleep(random.uniform(3,6))
            response_json=parse_logs()
            about_data=response_json['onResponseReceivedEndpoints'][0]['appendContinuationItemsAction']['continuationItems'][0]['aboutChannelRenderer']['metadata']
        except:
            about_data={'error':'Need to recheck'}
    else:
        about_data={'error':'This account has been terminated'}
    save_data(channelId,about_data)
    print(start_sub,end_sub)
