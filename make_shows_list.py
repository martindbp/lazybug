from wrapped_json import json
import glob

released_shows = {}
for filename in glob.glob('data/remote/public/shows/*.json'):
    with open(filename, 'r') as f:
        show_name = filename.split('/')[-1].split('.')[0]
        show = json.load(f)
        released_shows[show_name] = show

with open('data/remote/public/show_list.json', 'w') as f:
    json.dump(released_shows, f)
