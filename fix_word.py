import os
import sys
import glob
from wrapped_json import json

files = glob.glob(f'data/remote/public/subtitles/*.json')

for filename in files:
    if filename.endswith('merkl'):
        continue

    print('Processing', filename)

    with open(filename, 'r') as f:
        data = json.loads(f.read())

    for line in data['lines']:
        for i, word in enumerate(line[8]):
            try:
                if word[2] == '更' and word[3][0][1] == 'geng1':
                    word[3][0] = ['gèng', 'geng4']
                    print(line)
            except:
                pass

    with open(filename, 'w') as f:
        json.dump(data, f)
