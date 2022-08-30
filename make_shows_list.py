import os
import re
import sys
import glob
import subprocess
from collections import defaultdict
from wrapped_json import json
from scipy import optimize
import numpy as np
from han import CEDICT, make_cedict
from merkl import task, FileRef, Eval, pipeline

REQUIRED_FIELDS = ['year', 'type', 'genres', 'synopsis', 'douban', 'caption_source', 'translation_source', 'date_added']

# These bloom filter parameters are derived from 15k items with 1.0E-4 prob of false positive
# Source: https://hur.st/bloomfilter/?n=15000&p=1.0E-4&m=&k=
BLOOM_FILTER_N = 287552
BLOOM_FILTER_K = 13


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


@task
def get_show_stats(subtitle_paths, word_probs, min_prob):
    sum_information = 0
    sum_time = 0
    for subtitle_file in subtitle_paths:
        with open(subtitle_file) as f:
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
                    continue
            diff = t1-t0
            sum_time += diff

    if sum_time == 0:
        return None

    return sum_information / sum_time


@task
def get_sum_information(words, word_probs, min_prob):
    sum_information = 0
    for hz in words:
        prob = word_probs.get(hz, 0.01*min_prob)
        information = -np.log(prob)
        sum_information += information

    return sum_information


@task
def get_words_and_stats(subtitle_paths):
    sum_time = 0
    words = []
    for subtitle_file in subtitle_paths:
        with open(subtitle_file) as f:
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

                words.append(hz)

            if i < len(data['lines']) - 1:
                next_line = data['lines'][i+1]
                next_line_t0 = next_line[1][0]
                t1 = min(t1 + 5, next_line_t0)
                if t0 == 0 and i != 0:
                    continue
            diff = t1-t0
            sum_time += diff

    return words, sum_time


CHINESE_NUMBERS_REGEX = '^[一二三四五六七八九十百千万个]+$'

@task(deps=[FileRef('generate_bloom_filter.js')])
def get_bloom_filter(words, n, k, cedict, simple_chars):

    # Dedupe words
    words = list(set(words))

    # 1. Split compounds not in cedict
    # 2. Split words that are simple compounds
    new_words = set()
    for word in words:
        word = word.replace(' ', '')  # I've seen words with spaces

        if word in cedict or len(word) == 1:
            new_words.add(word)
            continue

        # Then check if it breaks down into components that are in cedict, or simple chars, or numbers
        max_length_squared = 0
        max_split = None
        for split_i in range(1, len(word)):
            pre, post = word[:split_i], word[split_i:]
            pre_is_number = re.match(CHINESE_NUMBERS_REGEX, pre)
            post_is_number = re.match(CHINESE_NUMBERS_REGEX, post)
            pre_is_simple = pre in simple_chars['pre'] or pre in simple_chars['pre_post']
            post_is_simple = post in simple_chars['post'] or post in simple_chars['pre_post']
            pre_ok = pre in cedict or pre_is_number or pre_is_simple
            post_ok = post in cedict or post_is_number or post_is_simple

            # We give extra weight to finding long numbers to fix this case:
            # '十五号' being split into 十 and 五号 because the latter is in cedict
            length_squared = len(pre) ** 2 + len(post) ** 2
            if pre_is_number:
                length_squared += len(pre)
            elif post_is_number:
                length_squared += len(post)

            if length_squared > max_length_squared and pre_ok and post_ok:
                max_length_squared = length_squared
                max_split = [pre, post]
                # Split numbers into individual chars
                if pre_is_number:
                    max_split = [*list(pre), post]
                elif post_is_number:
                    max_split = [pre, *list(post)]

        # Check simple middle
        for middle_i in range(1, len(word)-1):
            middle_char = word[middle_i]
            if middle_char not in simple_chars['middle']:
                continue
            pre, post = word[:middle_i], word[middle_i+1:]
            length_squared = len(pre) ** 2 + len(post) ** 2 + 1
            ok = pre + post in cedict
            if length_squared > max_length_squared and ok:
                max_length_squared = length_squared
                max_split = (pre, middle_char, post)

        if max_split is not None:
            for w in max_split:
                new_words.add(w)
            print(f'Splitting {word} -> {max_split}')
        else:
            new_words.add(word)

    words = list(new_words)

    words_file = FileRef()
    with open(words_file, 'w') as f:
        f.write('\n'.join(words))

    bloom_file = FileRef()

    command = ["node", "generate_bloom_filter.js", words_file, bloom_file, str(n), str(k)]
    print(' '.join(command))
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    for line in proc.stdout:
        sys.stdout.write(line.decode('utf-8'))

    text_widths = []
    with open(bloom_file, 'r') as f:
        bloom = f.read()

    os.remove(words_file)
    os.remove(bloom_file)
    return bloom


def make_shows_list():
    word_probs, min_prob = calc_word_probs()
    cedict = make_cedict()
    with open('data/remote/public/simple_chars.hash', 'r') as f:
        simple_chars_hash = f.read().strip()
    with open(f'data/remote/public/simple_chars-{simple_chars_hash}.json', 'r') as f:
        simple_chars = json.load(f)

    released_shows = {}
    bloom_filters = {'shows': {}, 'n': BLOOM_FILTER_N, 'k': BLOOM_FILTER_K}
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

            for required in REQUIRED_FIELDS:
                if required not in show:
                    print(f'ERROR: {required} not in show data for {show_name}')
                    sys.exit(1)

            if 'free' not in show:
                show['free'] = True

            # Calculate show difficulty
            subtitle_paths = []
            num_total, num_processed = 0, 0
            for season in show['seasons']:
                for episode in season['episodes']:
                    vid = episode['id']

                    hash_file = f'data/remote/public/subtitles/{vid}.hash'
                    num_total += 1
                    processed = os.path.exists(hash_file)
                    if not processed:
                        continue

                    with open(hash_file) as f:
                        hash = f.read().strip()

                    num_processed += 1
                    subtitle_file = f'data/remote/public/subtitles/{vid}-{hash}.json'
                    subtitle_paths.append(FileRef(subtitle_file))

            words, sum_time = get_words_and_stats(subtitle_paths)
            sum_time = sum_time.eval()

            score = get_sum_information(words, word_probs, min_prob).eval() / sum_time if sum_time != 0 else None
            if score is not None:
                show['num_processed'] = f'{num_processed}/{num_total}'
                print(show_name, 'score:', score)
                scores.append(score)
                show['difficulty'] = score

            bloom_filters['shows'][show_name] = get_bloom_filter(
                words,
                n=BLOOM_FILTER_N,
                k=BLOOM_FILTER_K,
                cedict=cedict,
                simple_chars=simple_chars
            ).eval()

            # Add processed flags for all episodes
            for season in show['seasons']:
                for episode in season['episodes']:
                    processed = os.path.exists(f'data/remote/public/subtitles/{episode["id"]}.hash')
                    episode['processed'] = processed

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

    with open('data/remote/public/bloom_filters.json', 'w') as f:
        json.dump(bloom_filters, f)

    print('Unreleased shows:')
    for show in unreleased:
        print(show)
