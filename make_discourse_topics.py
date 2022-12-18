import os
import sys
import glob
import discourse
import requests
from wrapped_json import json

DISCOURSE_API_KEY = os.getenv('DISCOURSE_API_KEY')
if DISCOURSE_API_KEY is None:
    print('DISCOURSE_API_KEY environment variable not set')
    sys.exit(1)

client = discourse.Client(
    host='https://discourse.lazybug.ai/',
    api_username='system',
    api_key=DISCOURSE_API_KEY,
)

category_id = [c for c in client.get_category_list() if c.slug == 'show-movie-discussions'][0].id
print('Category id', category_id)

if __name__ == "__main__":
    for filename in glob.glob('data/remote/public/shows/*.json'):
        show_name = filename.split('/')[-1].split('.')[0]
        print('Processing', show_name)
        with open(filename, 'r') as f:
            show = json.load(f)
        if not show.get('released', False):
            print(f'{show_name} not released, skipping')
            continue

        if show.get('discourse_topic_id', None) is not None:
            print(f'{show_name} already has discourse topic')
            continue

        try:
            topic = client.get_topic(show_name)
        except requests.exceptions.HTTPError:
            if isinstance(show['name'], dict):
                title = [show['name'].get('hz'), show['name'].get('py'), show['name'].get('en')]
                title = [n for n in title if n is not None]
                title = ' - '.join(title)
            else:
                title = show['name']

            if show['type'] == 'movie':
                raw = f'Description: {show["synopsis"]} \n[Link](https://lazybug.ai/player/{show_name}/)'
            else:
                raw = f'Description: {show["synopsis"]} \n[Link to first episode](https://lazybug.ai/player/{show_name}/1/1)'
            print('Creating', title, raw)

            # NOTE: client.create_topic is outdated, endpoint changed to /posts and
            # parameters are sent in body instead of query params
            #topic = client.create_topic(title, raw, category=category_id, created_at=None)
            response = client._request('POST', 'posts', data={
                'title': title,
                'raw': raw,
                'category': category_id,
                'draft_key': 'new_topic',
            })
            show['discourse_topic_id'] = response['topic_id']

        with open(filename, 'w') as f:
            json.dump(show, f)
