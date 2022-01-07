import re
import os
from wrapped_json import json
import glob
from collections import defaultdict
import numpy as np
from sklearn import tree
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import cross_val_score, LeaveOneOut
from sklearn.metrics import f1_score
from sklearn.ensemble import RandomForestClassifier

from pinyin import normalize_pinyin, extract_normalized_pinyin
from han import filter_text_hanzi, align_hanzi_and_pinyin, CEDICT

from transformer_segmentation import segment_sentences

from merkl import task, Eval, FileRef

@task(serializer=json, deps=[FileRef('data/remote/private/required/pinyin_freqs.txt')])
def make_pinyin_freq_db():
    pinyin_single = defaultdict(lambda: defaultdict(list))
    pinyin_all = defaultdict(lambda: defaultdict(list))

    sentences = []
    with open('data/remote/private/required/pinyin_freqs.txt', 'r') as f:
        lines = f.read().split('\n')
        lines = [line for line in lines if not line.startswith('#')]
        hzs = lines[::2]
        pys = lines[1::2]
        for hz, py in zip(hzs, pys):
            sentences.append({'hanzi': hz, 'pinyin': py})

    for transcript_file in glob.glob('data/remote/private/backup/chinesepod/transcripts/*.json'):
        filename = os.path.basename(transcript_file)
        print('Processing: ', filename)

        transcript = json.loads(open(transcript_file, 'r').read())
        sentences += transcript['sentences']

    hanzis = [s['hanzi'] for s in sentences]
    with Eval():
        segmentation = segment_sentences(hanzis, join_compound_words=False)

    compounds_out = []
    for sentence, (segs, poss, ners, people, compounds) in zip(sentences, segmentation):
        if 'pinyin' not in sentence:
            continue
        hanzi = sentence['hanzi']
        if len(compounds) > 0:
            compounds_translations = []
            for c, check_c in compounds:
                if check_c is None:
                    continue
                translations = ''
                for _, _, transl, _, _ in CEDICT.v[check_c][1]:
                    translations += transl
                compounds_translations.append((c, translations, True))
            compounds_out.append((hanzi, sentence.get('translation', ''), compounds_translations))

        hanzi = filter_text_hanzi(hanzi)
        pinyin = sentence['pinyin']
        pys = extract_normalized_pinyin(normalize_pinyin(pinyin))
        hanzi_pinyin_indices = align_hanzi_and_pinyin(hanzi, pys)

        i = 0
        next_i = 0
        for seg_i, (seg, pos) in enumerate(zip(segs, poss)):
            hz = filter_text_hanzi(seg[-1])
            if len(hz) == 0:
                continue

            i = next_i
            next_i = i + len(hz)

            try:
                pinyin_idx = hanzi_pinyin_indices[i]
            except:
                breakpoint()
                pass
            if pinyin_idx is None:
                # Was no levenshtein match
                continue

            pinyin_end_idx = hanzi_pinyin_indices[i + len(hz) - 1]
            if pinyin_end_idx is None:
                continue

            t_pys = pys[pinyin_idx : pinyin_end_idx + 1]

            if len(t_pys) != len(hz):
                # Skipped across missing stuff
                continue

            py = ''.join(t_pys).lower()
            exerpt = (hanzi, i, ''.join(pys), seg_i, segs, poss)

            if hz not in CEDICT.v:
                continue

            cedict_readings = [c[1].replace(' ', '') for c in CEDICT.v[hz][1]]

            if py not in cedict_readings:
                continue
            pinyin_single[hz][py].append(exerpt)

        for i, pinyin_idx in enumerate(hanzi_pinyin_indices):
            if pinyin_idx is None:
                # Was no levenshtein match
                continue

            hz = hanzi[i]
            py = pys[pinyin_idx].lower()
            exerpt = (hanzi, i, ''.join(pys), seg_i, segs, poss)
            pinyin_all[hz][py].append(exerpt)

    out = pinyin_all, pinyin_single
    return out
