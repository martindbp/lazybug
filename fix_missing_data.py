import os
import sys
from wrapped_json import json
from predict_video import predict_video_captions


def fix_missing_data(
    list_path: str,
    videos_path: str,
):
    with open(list_path, 'r') as f:
        video_ids = [vid for vid in f.read().split('\n') if vid.strip() != '']

    all_captions = []
    for video_id in video_ids:
        if video_id.startswith('#'):
            continue

        for fmt in ['mkv', 'webm', 'mp4']:
            video_path = os.path.join(videos_path, video_id + '.' + fmt)
            if os.path.exists(video_path):
                break
        else:
            video_path = None

        if video_path is None:
            print(f'Found no video for id {video_id}')
            continue

        caption_id = f'youtube-{video_id}'
        raw_captions_file = f'data/remote/private/caption_data/raw_captions/{caption_id}.json'
        data = None
        with open(raw_captions_file, 'r') as f:
            data = json.loads(f.read())
            lines = data['lines']
            has_many = False
            for line in lines:
                if len(line) > 0:
                    has_many = True

            if has_many:
                for line in lines:
                    if len(line) == 4:
                        line.append(None)
                        line.append(None)
                        line.append(None)

        with open(raw_captions_file, 'w') as f:
            json.dump(data, f)
            print(f'Fixed {raw_captions_file}')

    return all_captions
