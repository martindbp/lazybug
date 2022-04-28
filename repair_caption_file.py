import os
import sys
import glob
from wrapped_json import json

show_name = sys.argv[1]

video_ids = []
with open(f'data/remote/public/shows/{show_name}.json') as f:
    data = json.load(f)
    for season in data['seasons']:
        for episode in season['episodes']:
            video_ids.append(episode['id'])

files = []
for video_id in video_ids:
    files += glob.glob(f'data/remote/public/subtitles/{video_id}*.json')
    files += glob.glob(f'data/remote/private/caption_data/raw_captions/{video_id}*.json')
    files += glob.glob(f'data/remote/private/caption_data/meta_trimmed_captions/{video_id}*.json')
    files += glob.glob(f'data/remote/private/caption_data/captions_all_translations/{video_id}*.json')
    files += glob.glob(f'data/remote/private/caption_data/captions_human_translations/{video_id}*.json')


for filename in files:
    if filename.endswith('merkl'):
        continue

    print('Processing', filename)

    with open(filename, 'r') as f:
        data = json.loads(f.read())

    if 'frame_size' not in data or data['frame_size'] is None:
        continue

    y_offset = data['caption_top'] * data['frame_size'][0]
    is_already_absolute = False
    for line in data['lines']:
        rects = line[3] if isinstance(line[3][0], list) else [line[3]]

        for rect in rects:
            if rect is None or rect[0] is None:
                continue
            #print('Prev rect', rect)

            if rect[2] > 50:
                #print('Rect is already relative to 0,0')
                is_already_absolute = True
                break

            rect[2] += y_offset
            rect[3] += y_offset
            rect[2] = round(rect[2])
            rect[3] = round(rect[3])
            print('After rect', rect)

    data['version'] = 1
    data['show_name'] = show_name

    if not is_already_absolute:
        with open(filename, 'w') as f:
            json.dump(data, f)
