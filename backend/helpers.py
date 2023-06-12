import os
import json

from vars import *

def startup_tasks():
    if os.path.exists(VIDEOS_ROOT):
        print("VIDEOS_ROOT exists")
    else:
        print("VIDEOS_ROOT does not exist")
        os.mkdir(VIDEOS_ROOT)

    if os.path.exists(LOCAL_STORE_PATH):
        print("LOCAL_STORE_PATH exists")
        # TODO: check if it's a valid JSON file
        try:
            with open(LOCAL_STORE_PATH, 'r') as f:
                json.load(f)
        except json.decoder.JSONDecodeError:
            print("LOCAL_STORE_PATH is not a valid JSON file")
            with open(LOCAL_STORE_PATH, 'w') as f:
                f.write('{}')

    else:
        print("LOCAL_STORE_PATH does not exist")
        with open(LOCAL_STORE_PATH, 'w') as f:
            f.write('{}')
    
    # get the list of videos and store/update it in the json file
    videos = os.listdir(VIDEOS_ROOT)
    with open(LOCAL_STORE_PATH, 'r') as f:
        local_store = json.load(f)
    
    # check if local_store has key video
    if 'videos' not in local_store:
        local_store['videos'] = []
    
    if 'unlisted_videos' not in local_store:
        local_store['unlisted_videos'] = []

    print(local_store)

    for video in videos:
        if video not in local_store['videos'] and video not in local_store['unlisted_videos']:
            # append the video to the list
            local_store['videos'].append(video)

    with open(LOCAL_STORE_PATH, 'w') as f:
        json.dump(local_store, f, indent=4)

def get_next_video(current_video_index):
    with open(LOCAL_STORE_PATH, 'r') as f:
        local_store = json.load(f)
    
    if 'videos' not in local_store:
        raise Exception("No videos in the local store")
    
    if len(local_store['videos']) == 0:
        raise Exception("No videos in the local store")
    
    current_video_index += 1
    if current_video_index >= len(local_store['videos']):
        current_video_index = 0
    
    return {"video_id": current_video_index, "video_name": local_store['videos'][current_video_index]}
    
def get_video_list():
    with open(LOCAL_STORE_PATH, 'r') as f:
        local_store = json.load(f)
    
    if 'videos' not in local_store:
        raise Exception("No videos in the local store")
    
    return local_store

def playlist_index_swap(one, another):
    with open(LOCAL_STORE_PATH, 'r') as f:
        local_store = json.load(f)
    
    if 'videos' not in local_store:
        raise Exception("No videos in the local store")
    
    current_video_index = one
    another_video_index = another
    
    if current_video_index >= len(local_store['videos']):
        current_video_index = 0
    
    if another_video_index >= len(local_store['videos']):
        another_video_index = 0
    
    local_store['videos'][current_video_index], local_store['videos'][another_video_index] = local_store['videos'][another_video_index], local_store['videos'][current_video_index]

    with open(LOCAL_STORE_PATH, 'w') as f:
        json.dump(local_store, f, indent=4)
    
    return {"message": "success"}