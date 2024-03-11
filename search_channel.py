import requests
from headers import headers
import sqlite3
import json
import time
import random
from tqdm import tqdm

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()
def json_data_fetch():
    json_data = {
        'context': {
            'client': {
                'hl': 'en',
                'gl': 'SG',
                'deviceMake': '',
                'deviceModel': '',
                'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36,gzip(gfe)',
                'clientName': 'WEB',
                'clientVersion': '2.20240222.08.00',
                'osName': 'Windows',
                'osVersion': '10.0',
                'originalUrl': 'https://www.youtube.com/results?search_query=gaming&sp=EgIQAg%253D%253D',
                'platform': 'DESKTOP',
                'clientFormFactor': 'UNKNOWN_FORM_FACTOR',
                'userInterfaceTheme': 'USER_INTERFACE_THEME_DARK',
                'timeZone': 'Asia/Dhaka',
                'browserName': 'Chrome',
                'browserVersion': '121.0.0.0',
                'acceptHeader': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'screenWidthPoints': 998,
                'screenHeightPoints': 932,
                'screenPixelDensity': 1,
                'screenDensityFloat': 1,
                'utcOffsetMinutes': 360,
                'connectionType': 'CONN_CELLULAR_4G',
                'memoryTotalKbytes': '8000000',
                'mainAppWebInfo': {
                    'graftUrl': 'https://www.youtube.com/results?search_query=gaming&sp=EgIQAg%253D%253D',
                    'pwaInstallabilityStatus': 'PWA_INSTALLABILITY_STATUS_UNKNOWN',
                    'webDisplayMode': 'WEB_DISPLAY_MODE_BROWSER',
                    'isWebNativeShareAvailable': True,
                },
            },
            'user': {
                'lockedSafetyMode': False,
            },
            'request': {
                'useSsl': True,
                'internalExperimentFlags': [],
                'consistencyTokenJars': [],
            },
        }
    }
    return json_data

params = {
    'prettyPrint': 'false',
}

def initial_query(keyword,json_data):
    json_data['query']=keyword
    json_data['params']='EgIQAg%3D%3D'
    response = requests.post(
        'https://www.youtube.com/youtubei/v1/search',
        params=params,
        headers=headers,
        json=json_data,
    )
    response_full=response.json()
    continuation=response_full['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][1]['continuationItemRenderer']['continuationEndpoint']['continuationCommand']['token']
    response_contents=response_full['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
    channel_list=[]
    for each_channel in response_contents:
        if 'channelRenderer' in str(each_channel):
            channel_list.append(each_channel['channelRenderer'])
    return continuation,channel_list

def next_pages(continuation,json_data):
    json_data['continuation']=continuation
    response = requests.post(
        'https://www.youtube.com/youtubei/v1/search',
        params=params,
        headers=headers,
        json=json_data,
    )
    response_full=response.json()
    if 'No more results' in str(response_full['onResponseReceivedCommands'][0]['appendContinuationItemsAction']['continuationItems']):
        continuation=None
    else:
        continuation=response_full['onResponseReceivedCommands'][0]['appendContinuationItemsAction']['continuationItems'][1]['continuationItemRenderer']['continuationEndpoint']['continuationCommand']['token']
    if 'No more results' not in str(response_full['onResponseReceivedCommands'][0]['appendContinuationItemsAction']['continuationItems'][0]['itemSectionRenderer']['contents']):
        response_contents=response_full['onResponseReceivedCommands'][0]['appendContinuationItemsAction']['continuationItems'][0]['itemSectionRenderer']['contents']
        channel_list=[]
        for each_channel in response_contents:
            if 'channelRenderer' in str(each_channel):
                channel_list.append(each_channel['channelRenderer'])
    else:
        channel_list=None
    return continuation,channel_list


def save_channels(channel_list):
    for each_channel in channel_list:
        sqlite_insert_with_param = """INSERT OR IGNORE INTO channels
                                (channelId,data) 
                                VALUES (?,?);"""
        data_tuple = (each_channel['channelId'],json.dumps(each_channel))
        cursor.execute(sqlite_insert_with_param, data_tuple)
        conn.commit()

keywords=["shortsbeta","shortsart","shortscooking","shortschallenge","youtuberlikes"]

for keyword in tqdm(keywords):
    print(keyword)
    json_data=json_data_fetch()
    continuation,channel_list=initial_query(keyword,json_data)
    save_channels(channel_list)
    json_data=json_data_fetch()
    while True:
        if continuation:
            continuation,channel_list=next_pages(continuation,json_data)
            if channel_list:
                save_channels(channel_list)
            if continuation:
                with open("continuation_search.txt", "w") as text_file:
                    text_file.write(continuation)
            time.sleep(random.uniform(5,20))
        else:
            break


conn.close()