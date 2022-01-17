import os
import sys
import yaml
from predict_video import predict_video_captions
from levenshtein import weighted_levenshtein

from predict_video import get_video_length_size


def trim_ends(
    list_path: str,
    videos_path: str,
    offset_start: float,
    offset_end: float,
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

        video_length, _ = get_video_length_size(video_path)

        caption_id = f'youtube-{video_id}'
        raw_captions_file = f'data/remote/private/caption_data/raw_captions/{caption_id}.yaml'
        redo_sections = []
        data = None
        with open(raw_captions_file, 'r') as f:
            data = yaml.loads(f.read())
            lines = data['lines']

            new_lines = []
            for line in lines:
                if line[1] < offset_start or line[2] > video_length - offset_end:
                    print(f'Trimming {line}')
                    continue
                print(f'Keeping {line}')
                new_lines.append(line)

            data['lines'] = new_lines

        with open(raw_captions_file, 'w') as f:
            yaml.dump(data, f)

    return all_captions
