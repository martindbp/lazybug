import os
import sys
import glob
import random
import discourse
import requests
from wrapped_json import json
import pyperclip

prompt = """
Classify the difficulty of the TV show based on this excerpt:
{}

Use the following grading levels:
Difficulty 1: Very simple language like a TV show for 2-3 year-olds, or beginner learning material
Difficulty 2: Equivalent to TV shows for preschool-age children, such as Peppa Pig, or material for lower intermediate learners
Difficulty 3: TV for adults such as dramas or comedy with fairly simple everyday language, such as the show "Friends"
Difficulty 4: Slightly more advanced material and grammar, but not requiring overly specific cultural knowledge
Difficulty 5: Native level material that requires cultural or highly specific vocabulary, such as history themed shows or deeply technical material

Give one difficulty level for all the sentences on the format "Difficulty: X". Include a decimal point if the difficulty falls between levels.
"""

SAMPLE_NUM_EXCERPTS = 1
EXCERPT_SIZE = 30

if __name__ == "__main__":
    for filename in glob.glob('data/git/shows/*.json'):
        show_name = filename.split('/')[-1].split('.')[0]
        print('Processing', show_name)
        with open(filename, 'r') as f:
            show = json.load(f)
        if not show.get('released', False):
            print(f'{show_name} not released, skipping')
            continue

        if show.get('difficulty', None) is not None:
            print(f'{show_name} already has difficulty set')
            continue

        all_episode_ids = []
        for season in show['seasons']:
            for episode in season['episodes']:
                hash_file = f'data/remote/public/subtitles/{episode["id"]}.hash'
                if os.path.exists(hash_file):
                    all_episode_ids.append(episode['id'])

        random.shuffle(all_episode_ids)
        random_episode_ids = all_episode_ids[:SAMPLE_NUM_EXCERPTS]

        difficulties = []
        for episode_id in random_episode_ids:
            hash_file = f'data/remote/public/subtitles/{episode_id}.hash'
            with open(hash_file) as f:
                hash = f.read().strip()
            subtitle_file = f'data/remote/public/subtitles/{episode_id}-{hash}.json'
            with open(subtitle_file) as f:
                data = json.load(f)
                mid = len(data['lines']) // 2  # sample from middle of episode
                lines = ''
                for line in data['lines'][mid:mid + EXCERPT_SIZE]:
                    text = line[0][0]
                    lines += text + '\n'

                print('Copy paste the following into ChatGPT:')
                p = prompt.replace('{}', lines)
                print(p)
                pyperclip.copy(p)
                difficulty = input('Difficulty: ')
                difficulties.append(float(difficulty))

        show['difficulty'] = sum(difficulties) / len(difficulties)
        with open(filename, 'w') as f:
            json.dump(show, f)
