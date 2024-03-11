from botasaurus import *
from botasaurus.create_stealth_driver import create_stealth_driver
import sqlite3
import random
import time

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

def queue_list():
    # Execute the SQL query
    query = f"""
    SELECT 
    channelId,
    json_extract(data, '$.aboutChannelViewModel.joinedDateText.content') AS joinedDate,
    json_extract(data, '$.aboutChannelViewModel.country') AS country,
    json_extract(data, '$.aboutChannelViewModel.subscriberCountText') AS subscriberCountText,
    json_extract(data, '$.aboutChannelViewModel.viewCountText') AS viewCountText,
    json_extract(data, '$.aboutChannelViewModel.videoCountText') AS videoCountText,
    json_extract(data, '$.aboutChannelViewModel.description') AS description,
    channelId
    FROM channel_details
    WHERE joinedDate like '%2023%' and channelId not in (Select channelId from socialblade_links)
    ;
    """
    cursor.execute(query)
    # Fetch the results
    results = cursor.fetchall()
    results=[i[0] for i in results]
    return results

def save_data(channelId):
    sqlite_insert_with_param = """INSERT OR IGNORE INTO socialblade_links
                                    (channelId) 
                                    VALUES (?);"""
    data_tuple = (channelId,)
    cursor.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()
    print('Crawled : ',channelId)


def split_list(input_list, n):
    return [input_list[i:i + n] for i in range(0, len(input_list), n)]

def scraping_task(queue_chunk,headless):
    @browser(
    headless=headless, 
    max_retry=5,
    reuse_driver=True,
    data=queue_chunk,
    create_driver=create_stealth_driver(
        wait=4,
        start_url=f'https://socialblade.com/youtube/channel/{queue_chunk[0]}/similarrank',
        raise_exception=True,
    ),
    )
    def scrape_heading_task(driver: AntiDetectDriver, data):
        driver.get(f'https://socialblade.com/youtube/channel/{data}/similarrank')
        time.sleep(random.uniform(2,5))
        places_links_selector = '#socialblade-user-content > div > a'
        links= driver.links(places_links_selector)
        for link in links:
            channelId=link.split('/')[-1]
            save_data(channelId)
        time.sleep(random.uniform(2,5))
    scrape_heading_task()    
sublist_length = 5

queue=queue_list()
queue=split_list(queue, sublist_length)

for queue_chunk in queue:
    scraping_task(queue_chunk,False)
