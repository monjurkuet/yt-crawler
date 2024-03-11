from selenium import webdriver
import json
import time
import sqlite3
import random
from tqdm import tqdm

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

def queue_list():
    # Execute the SQL query
    query = """
    SELECT channelId from socialblade_links WHERE channelId like 'U%' and channelId not like  '%youtube' and length(channelId)>15 and channelId not in (Select channelId from channel_details)
    """
    cursor.execute(query)
    # Fetch the results
    results = cursor.fetchall()
    results=[i[0] for i in results]
    return results

def parse_logs(driver):
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

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    #proxy_server = "127.0.0.1:16379"
    #options.add_argument(f'--proxy-server={proxy_server}')
    options.add_argument("--mute-audio")
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    return webdriver.Chrome(options=options)

def process_chanels(channelId_queue):
    driver=get_driver()
    counter=0
    for channelId in tqdm(channelId_queue):
        print('Crawling : ',f'https://www.youtube.com/channel/{channelId}')
        counter+=1
        if counter%200==0:
            driver.close()
            driver.quit()
            driver=get_driver()
        driver.get(f'https://www.youtube.com/channel/{channelId}')
        time.sleep(random.uniform(4,7))
        if 'This channel does not exist.' in driver.page_source:
            about_data={'error':'This channel does not exist.'}
        elif 'This account has been terminated' in driver.page_source:
            about_data={'error':'This account has been terminated'}
        else:
            driver.find_element('xpath','//yt-icon[@id="more-icon"]').click()
            time.sleep(random.uniform(3,6))
            response_json=parse_logs(driver)
            about_data=response_json['onResponseReceivedEndpoints'][0]['appendContinuationItemsAction']['continuationItems'][0]['aboutChannelRenderer']['metadata']
        save_data(channelId,about_data)
        print(about_data)
        print('Crawled : ',channelId)
    driver.close()
    driver.quit()


if __name__ == "__main__":
    channelId_queue=queue_list() # get list of unprocessed data from queue
    process_chanels(channelId_queue)

