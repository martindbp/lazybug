import os
from wrapped_json import json
import glob

for filename in glob.glob('data/remote/private/caption_data/raw_captions/*.json'):
    if filename.endswith('merkl'):
        continue

    with open(filename, 'r') as f:
        data = json.loads(f.read())

    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
