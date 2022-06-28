import os
import sys
import glob
from collections import defaultdict
from wrapped_json import json
from scipy import optimize
import numpy as np
from han import CEDICT
from merkl import task, FileRef, Eval


def get_video_data(vid):
    hash_file = f'data/remote/public/subtitles/{vid}.hash'
    if not os.path.exists(hash_file):
        return None

    with open(f'data/remote/public/subtitles/{vid}.hash') as f:
        hash = f.read().strip()

    with open(f'data/remote/public/subtitles/{vid}-{hash}.json') as f:
        data = json.load(f)
        return data


# Build frequency database for words by using children's cartoons only, weighted by their perceived difficulty (by me)

@task(deps=[FileRef(f) for f in glob.glob('data/remote/public/shows/*.json')])
def calc_word_probs():
    word_freqs = defaultdict(lambda: 0)
    weights = {
        'xiaozhupeiqi': 5,
        'yingtaoxiaowanzi': 5,
        'hongmaolantu': 5,
        'daerduotutu': 5,
    }
    #for show_name in ['xiaozhupeiqi', 'yingtaoxiaowanzi', 'hongmaolantu', 'daerduotutu']:
        #filename = f'data/remote/public/shows/{show_name}.json'
    for filename in glob.glob('data/remote/public/shows/*.json'):
        with open(filename, 'r') as f:
            show_name = filename.split('/')[-1].split('.')[0]
            show = json.load(f)
            video_ids = []
            for season in show['seasons']:
                for episode in season['episodes']:
                    video_ids.append(episode['id'])

            weight = weights.get(show_name, 1)
            for vid in video_ids:
                data = get_video_data(vid)
                if data is None:
                    continue

                for line in data['lines']:
                    alignments = line[8]
                    for word in alignments:
                        hz = word[2]
                        tr = word[-1]
                        if len(word[-1]) == 0:
                            continue

                        is_name = word[-1][0].isupper() and tr !='I' and tr != "I'm" and tr != "OK"
                        if is_name:
                            #print(f'Skipping {hz}, name')
                            continue

                        word_freqs[hz] += weight

    sum_word_freqs = sum(word_freqs.values())
    word_probs = {hz: val / sum_word_freqs for hz, val in word_freqs.items()}
    min_prob = min(word_probs.values())
    return word_probs, min_prob


with Eval():
    word_probs, min_prob = calc_word_probs()


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
    num_processed = 0
    num_total = 0
    sum_information = 0
    sum_time = 0
    for vid in video_ids:
        hash_file = f'data/remote/public/subtitles/{vid}.hash'
        num_total += 1
        if not os.path.exists(hash_file):
            #print(hash_file, 'does not exist, skipping')
            continue

        num_processed += 1

        with open(f'data/remote/public/subtitles/{vid}.hash') as f:
            hash = f.read().strip()

        with open(f'data/remote/public/subtitles/{vid}-{hash}.json') as f:
            data = json.load(f)

        for i, line in enumerate(data['lines']):
            t0 = line[1][0]
            t1 = line[2][-1]
            alignments = line[8]
            max_line_information = 0
            max_line_word = None
            for word in alignments:
                hz = word[2]
                tr = word[-1]
                if len(word[-1]) == 0:
                    continue

                is_name = word[-1][0].isupper() and tr !='I' and tr != "I'm" and tr != "OK"
                if is_name:
                    continue

                prob = word_probs.get(hz, 0.01*min_prob)
                information = -np.log(prob)
                sum_information += information

            if i < len(data['lines']) - 1:
                next_line = data['lines'][i+1]
                next_line_t0 = next_line[1][0]
                t1 = min(t1 + 5, next_line_t0)
                if t0 == 0 and i != 0:
                    #breakpoint()
                    continue
            diff = t1-t0
            sum_time += diff

    if sum_time == 0:
        return None, None, None

    return sum_information / sum_time, num_processed, num_total

required_data = ['year', 'type', 'genres', 'synopsis', 'douban', 'caption_source', 'translation_source']

released_shows = {}
unreleased = []
scores = []
for filename in glob.glob('data/remote/public/shows/*.json'):
    with open(filename, 'r') as f:
        show_name = filename.split('/')[-1].split('.')[0]
        print('Processing', show_name)
        show = json.load(f)
        if not show.get('released', False):
            unreleased.append(show_name)
            continue

        if not show['name'] or (isinstance(show['name'], dict) and (not show['name']['hz'] or not show['name']['py'] or not show['name']['en'])):
            print('ERROR No name for show:', show_name)
            sys.exit(1)

        for required in required_data:
            if required not in show:
                print(f'ERROR: {required} not in show data for {show_name}')
                sys.exit(1)

        # Calculate show difficulty
        video_ids = []
        for season in show['seasons']:
            for episode in season['episodes']:
                video_ids.append(episode['id'])

        score, num_processed, num_total = get_show_stats(video_ids)
        if score is not None:
            show['num_processed'] = f'{num_processed}/{num_total}'
            print(show_name, 'score:', score)
            scores.append(score)
            show['difficulty'] = score

        released_shows[show_name] = show

scores = np.array(scores)
mean_scores = scores.mean()
std_scores = scores.std()

# Normalize the difficulty scores
for name, show in released_shows.items():
    if 'difficulty' not in show:
        if 'difficulty_manual' not in show:
            print('ERROR', name, 'has no difficulty score, need to set difficulty_manual')
            sys.exit(1)
        continue
    score = (min(max(-2, (show['difficulty'] - mean_scores) / 4), 2) + 2) / 4
    show['difficulty']  = score
    print(name, show['difficulty'])

with open('data/remote/public/show_list_full.json', 'w') as f:
    json.dump(released_shows, f)

print('Unreleased shows:')
for show in unreleased:
    print(show)
