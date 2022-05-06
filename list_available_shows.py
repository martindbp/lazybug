import json
import glob

for filename in glob.glob('data/remote/public/shows/*.json'):
    with open(filename, 'r') as f:
        released = json.load(f).get('released', False)

        if released:
            print(filename)
