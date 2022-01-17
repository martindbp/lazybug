import os
from wrapped_json import json
import glob

for filename in glob.glob('data/remote/private/caption_data/raw_captions/*.json'):
    if filename.endswith('merkl'):
        continue

    with open(filename, 'r') as f:
        data = json.loads(f.read())

    if not isinstance(data['caption_top'], float):
        data['caption_top'] /= data['frame_size'][0]
        print(data['caption_top'])

    with open(filename, 'w') as f:
        json.dump(data, f)
