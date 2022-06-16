import os
import sys
import glob
from wrapped_json import json
from scipy import optimize
import numpy as np

def get_show_stats(video_ids):
    hsk_levels = {}
    with open('data/git/hsk_words.json', 'r') as f:
        hsk = json.load(f)
        for lvl, words in enumerate(hsk):
            for word in words:
                hsk_levels[word] = lvl + 1

    seen_words = set()
    new_words_per_hour = []
    new_weighted_words_per_hour = []
    last_t = []
    t_offset = 0
    BUCKET_SIZE = 60*60 # quarter hour
    for vid in video_ids:
        hash_file = f'data/remote/public/subtitles/{vid}.hash'
        if not os.path.exists(hash_file):
            #print(hash_file, 'does not exist, skipping')
            continue

        with open(f'data/remote/public/subtitles/{vid}.hash') as f:
            hash = f.read().strip()

        with open(f'data/remote/public/subtitles/{vid}-{hash}.json') as f:
            data = json.load(f)

        hour = 0
        for line in data['lines']:
            t = line[1][0]
            alignments = line[8]
            for word in alignments:
                hz = word[2]
                if hz in seen_words:
                    continue
                seen_words.add(hz)

                hour = int((t + t_offset) // (BUCKET_SIZE))
                if hour >= len(new_words_per_hour):
                    new_words_per_hour.append(0)
                    new_weighted_words_per_hour.append(0)
                    last_t.append(0)

                new_words_per_hour[hour] += 1
                #print('Saw', hz, hsk_levels.get(hz, None))
                new_weighted_words_per_hour[hour] += pow(hsk_levels.get(hz, 0), 2) / pow(6, 2)
                last_t[hour] = t + t_offset

        if len(data['lines']) > 0:
            t_offset += t

    for hour in range(len(new_words_per_hour)):
        #print(new_words_per_hour[hour], (hour+1)*BUCKET_SIZE, last_t[hour], 1-((hour+1)*BUCKET_SIZE - last_t[hour]) / (BUCKET_SIZE))
        normalizing_factor = 1 - ((hour+1)*BUCKET_SIZE - last_t[hour]) / (BUCKET_SIZE)
        new_words_per_hour[hour] /= normalizing_factor
        new_weighted_words_per_hour[hour] /= normalizing_factor

    score = None
    if len(new_words_per_hour) > 0:
        try:
            fit = optimize.curve_fit(
                lambda t,a,b,c: a*np.exp(-t/b) + c,
                list(range(len(new_weighted_words_per_hour))),
                new_words_per_hour, 
                p0=(new_words_per_hour[0], 5, 0)
            )[0]
            score = (fit[0] + 2*fit[1]) / 2
        except:
            pass

    return new_words_per_hour, new_weighted_words_per_hour, score


released_shows = {}
min_score, max_score = float('inf'), 0
for filename in glob.glob('data/remote/public/shows/*.json'):
    with open(filename, 'r') as f:
        show_name = filename.split('/')[-1].split('.')[0]
        print('Processing', show_name)
        show = json.load(f)
        if show.get('released', False) and not show['name'] or (isinstance(show['name'], dict) and (not show['name']['hz'] or not show['name']['py'] or not show['name']['en'])):
            print('ERROR No name for show:', show_name)
            continue

        # Calculate show difficulty

        video_ids = []
        for season in show['seasons']:
            for episode in season['episodes']:
                video_ids.append(episode['id'])

        stats, stats_hsk, score = get_show_stats(video_ids)
        print(show_name, 'score:', score)
        if score is not None:
            min_score = min(min_score, score)
            max_score = max(max_score, score)
            show['difficulty'] = score

        released_shows[show_name] = show

# Normalize the difficulty scores
for name, show in released_shows.items():
    if 'difficulty' not in show:
        if 'difficulty_manual' not in show:
            print('ERROR', name, 'has no difficulty score, need to set difficulty_manual')
        continue
    show['difficulty']  = (show['difficulty'] - min_score) / (max_score - min_score)
    print(name, show['difficulty'])

with open('data/remote/public/show_list_full.json', 'w') as f:
    json.dump(released_shows, f)
