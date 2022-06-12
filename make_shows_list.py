import sys
import glob
from wrapped_json import json

released_shows = {}
for filename in glob.glob('data/remote/public/shows/*.json'):
    with open(filename, 'r') as f:
        show_name = filename.split('/')[-1].split('.')[0]
        show = json.load(f)
        released_shows[show_name] = show
        if show.get('released', False) and not show['name'] or (isinstance(show['name'], dict) and (not show['name']['hz'] or not show['name']['py'] or not show['name']['en'])):
            print('ERROR No name for show:', show_name)
            sys.exit(1)

with open('data/remote/public/show_list.json', 'w') as f:
    json.dump(released_shows, f)
