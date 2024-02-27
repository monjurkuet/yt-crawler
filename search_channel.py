import requests
from headers import headers
import sqlite3
import json
import time
import random

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

keywords=["live","gaming","amongus","gameplay","gametv","youtubegamer","livegaming","gamereview","gamecommentary","livestream","youtubegaming","gamer","ps","twitch","gamingcommunity","youtubegamingchannel","xbox","playstation","playfortnite","videogames","pcgaming","youtubegamers","twitchstreamer","gameplay","streamer","minecraft","pubg","tastyrecipes","cook","chef","homemade","foodie","foodlover","recipes","diet","healthylifestyle","fastfood","homemadecooking","homemadewithlove","yummy","foodblogger","delicious","healthyfood","dinner","tasty","bgmi","bgmindia","pubgfunny","pubgm","bgmimemes","bgmimontage","bgmilovers","pubgbattlegrounds","pubggameplay","pubggame","bgmiclips","pubgmindia","pubgmixer","tbgmidfest","bgmix","rbgminded","beautyskin","beautyhacks","skincarereview","modelslife","indianmodels","beautytip","beautyconsultant","beautyface","skincareroutines","beautyobsessed","beautystudio","makeupvideos","makeuprevolution","naturalbeauty","urbandecay","makeuptutorial","fun","live","funny","comedy","lol","meme","trending","memes","subscriber","Youtub","gamecommunity","shortstiktok","funnyvideos","comedyvideos","lmao","laugh","tech","techreview","technews","smartphone","techtips","techyoutuber","mobile","techie","meta","creators","metaverse","technogamerz","technologynews","techgadgets","android","techvideos","smartgadgets","gadgetsnews","teaching","learning","facts","support","goals","like","nonprofit","career","educationmatters","technology","newtechnology","techblogger","techtrends","educational","education","learn","knowledge","qualityeducation","currentaffairs","didyouknow","gk","educateyourself","youtube","youtuber","subscribe","youtubelikes","youtubevide","youtubemarketing","youtubeviews","instavideo","instayoutube","youtubeindia","youtubeuse","youtubelife","youtubesubscribers","youtubelive","youtubecreator","youtuberewind","youtuberp","youtubepremium","subscribers","subscriberyoutube","subscribersyoutube","100subscribers","200subscribers","500subscribers","1ksubscribers","10ksubscribers","100ksubscribers","1millionsubscribers","3millionsubscribers","10millionsubscribers","subscribersonly","freesubscribers","getsubscribers","subscribersrock","moresubscribers","influencer","digitalinfluencer","influencers","fashioninfluencer","styleinfluencer","beautyinfluencer","influencermarketing","influencerstyle","hinfluencercollective","minidigitalinfluencer","influencerdigital","doginfluencer","microinfluencer","travelinfluencer","influencerswanted","video","vlog","life","youtubechannel","twitch","viral","newvide","motivation","motivationalvideos","motivational","motivationalspeaker","motivationalvideo","inspiration","success","inspirational","nevergiveup","lifestory","lifehack","lifetips","lifegyan","lifegoeson","lifestyle","lifestylevlog","youtubevideos","youtubemusic","art","artist","myart","abstractart","artsy","practice","visualart","artoftheday","onlineart","artvideo","videoart","digitalart","artlife","modernart","arttutorial","creative","gallery","fineart","artstudio","spotify","music","newmusic","hiphop","rap","musicvideo","beats","musician","youtubecommunity","song","rapmusic","musicproducer","youtubeblack","songwriter","musical","dankmemes","funnymemes","memer","youtubememes","favoritememes","memewar","justmemes","newvideo","share","youtubers","love","shorts","funnyshorts","alpha","tiktok","gameplay","explore","sub","youtubeguru","youtubeislife","shortsfunny","shortsbgm","shortscomedy","shortsbts","shortsasmr","shortsadoptme","shortsanity","shortsbeta","shortsart","shortscooking","shortschallenge","youtuberlikes"]

for keyword in keywords:
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