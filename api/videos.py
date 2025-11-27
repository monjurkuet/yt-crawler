import requests
import json

def get_videos(channel_id):
    headers = {
        'content-type': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'origin': 'https://www.youtube.com',
        'referer': 'https://www.youtube.com/',
    }

    json_data = {
        'context': {
            'client': {
                'clientName': 'WEB',
                'clientVersion': '2.20251125.06.00',
            },
        },
        'browseId': channel_id,
        'params': 'EgZ2aWRlb3PyBgQKAjoA',
    }

    try:
        response = requests.post(
            'https://www.youtube.com/youtubei/v1/browse',
            headers=headers,
            json=json_data,
        )
        response.raise_for_status()
        data = response.json()
        
        extracted_videos = []
        
        # Navigate to the tabs
        tabs = data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])
        
        for tab in tabs:
            # Find the selected tab (which should be Videos due to params)
            if tab.get('tabRenderer', {}).get('selected'):
                content = tab.get('tabRenderer', {}).get('content')
                if content and 'richGridRenderer' in content:
                    items = content['richGridRenderer'].get('contents', [])
                    
                    for item in items:
                        if 'richItemRenderer' in item:
                            video = item['richItemRenderer'].get('content', {}).get('videoRenderer', {})
                            if video:
                                video_id = video.get('videoId')
                                published_time = video.get('publishedTimeText', {}).get('simpleText')
                                view_count = video.get('viewCountText', {}).get('simpleText')
                                
                                video_info = {
                                    'video_id': video_id,
                                    'published_time': published_time,
                                    'view_count': view_count
                                }
                                extracted_videos.append(video_info)
                break
        
        return extracted_videos

    except Exception as e:
        print(f"Error fetching videos: {e}")
        return []

if __name__ == "__main__":
    channel_id = 'UCnwxzpFzZNtLH8NgTeAROFA'
    videos = get_videos(channel_id)
    print(json.dumps(videos, indent=2))