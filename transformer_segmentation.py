import re
import os
import itertools
import torch
from hanziconv import HanziConv
from typing import *
from merkl import task, batch, Eval, Future

from han import filter_text_hanzi, is_name_according_to_cedict, get_difficulty, CEDICT
from word_disambiguation import pad_parts_of_speech, construct_classifier_args
from pinyin import (
    extract_normalized_pinyin,
    pinyin_wade_giles_conversion_table,
    wade_giles_pinyin_conversion_table,
    PINYIN_SYLLABLES,
    WADE_GILES_SYLLABLES,
)

from pinyin_classifiers import exec_code

os.environ["TRANSFORMERS_CACHE"] = "./data/local/huggingface-models/"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger, CkipNerChunker
import jieba_fast as jieba

ws_driver = None
pos_driver = None
ner_driver = None

PINYIN_CLASSIFIERS = Future.from_file('data/git/pinyin_classifiers.py', raise_file_not_found=False)

def cedict_max_freq_pinyin(hz, match_py_syllable=None):
    # NOTE: if match_py_syllable is provided, we want to match this specific syllable
    if hz not in CEDICT.v:
        return None

    entries = CEDICT.v.get(hz)
    entries = entries[1]
    max_freq_py = None
    max_freq = -1
    for _, py, _, freq, _ in entries:
        if match_py_syllable is not None and re.search(f'{match_py_syllable}[1-5]*', py.lower()) is None:
            continue

        if freq is None and max_freq < 0:
            max_freq_py = py
        elif (
            freq > max_freq or
            (freq == max_freq and py[0].islower())  # prioritize non-names
        ):
            max_freq = freq
            max_freq_py = py

    return max_freq_py


def cedict_all_possible_pinyins(hz, split=True, no_tone=True, lower=True):
    all_char_pys = []
    for char in hz:
        entries = CEDICT.v.get(char)
        if entries == None:
            all_char_pys.append([char])
            continue
        entries = entries[1]
        char_pys = []
        for _, py, _, freq, _ in entries:
            if len(extract_normalized_pinyin(py)) != len(char):
                continue
            if no_tone:
                py = re.sub('[1-5]', '', py)
            if lower:
                py = py.lower()
            char_pys.append(py)

        all_char_pys.append(list(set(char_pys)))

    combinations = list(itertools.islice(itertools.product(*all_char_pys), 10000))

    final_pys = []
    for py in combinations:
        if split:
            final_pys.append(list(py))
        else:
            final_pys.append(''.join(py))

    return final_pys


def hz_to_py(hz, hzs, sentence_psos, idx, classifiers):
    if hz in classifiers:
        classifier = classifiers[hz]
        args = construct_classifier_args(hzs, sentence_psos, idx)
        cl_py = classifier(*args)
        return cl_py
    elif hz in classifiers['single_readings']:
        cl_py = classifiers['single_readings'][hz]
        return cl_py
    else:
        py = cedict_max_freq_pinyin(hz)
        if py == None:
            # This only happens when we've got some really weird character from OCR, so it's probably garbage. But we
            # need to return something
            return 'he1'*len(hz)
        return py


@task(deps=[cedict_max_freq_pinyin])
def segmentations_to_pinyin(segmentations):
    if PINYIN_CLASSIFIERS is not None:
        classifiers = exec_code(PINYIN_CLASSIFIERS.v)

    all_pys = []
    for sentence_segs, sentence_psos, *_ in segmentations:
        sentence_pys = []
        hzs = [seg[-1].strip() for seg in sentence_segs]
        for idx, (seg, pos) in enumerate(zip(sentence_segs, sentence_psos)):
            hz = seg[-1].strip()
            if len(filter_text_hanzi(hz)) == 0:
                sentence_pys.append('')
                continue

            if hz in CEDICT.v:
                sentence_pys.append(hz_to_py(hz, hzs, sentence_psos, idx, classifiers))
            else:
                # Break down further
                tokens = []
                for start_idx in range(len(hz)):
                    for end_idx in range(start_idx+1, len(hz)+1):
                        sub_hz = hz[start_idx:end_idx]
                        if sub_hz in CEDICT.v:
                            tokens.append((sub_hz, start_idx, end_idx))

                # Check longest tokens first
                tokens = list(sorted(tokens, key=lambda x: x[2] - x[1], reverse=True))

                taken = [False] * len(hz)
                idx_matches = []
                for t, start_idx, end_idx in tokens:
                    if True in taken[start_idx:end_idx]:
                        # Already taken
                        continue
                    # Take/assign
                    taken[start_idx:end_idx] = [True] * (end_idx - start_idx)
                    idx_matches.append((start_idx, t))

                # Add single character words that haven't been taken
                for i, (char, char_taken) in enumerate(zip(hz, taken)):
                    if len(filter_text_hanzi(char)) == 0:
                        continue
                    if not char_taken:
                        non_hanzi_chars = i - len(filter_text_hanzi(hz[:i]))
                        idx_matches.append((i, char))

                word_pys = []
                for match_idx, match_hz in sorted(idx_matches, key=lambda x: x[0]):
                    word_pys.append(hz_to_py(match_hz, hzs, sentence_psos, idx, classifiers))

                # Convert all but first pys to lower in case they start with upper case
                for i, py in enumerate(word_pys):
                    if i == 0:
                        continue
                    word_pys[i] = py.lower()

                # Apply special cases here:
                if idx_matches[-1][1] == '长' and hz not in CEDICT.v:
                    # For example: 护士长 should be hu4shi5zhang3, not hu4shi5zhang3
                    word_pys[-1] = 'zhang3'

                sentence_pys.append(''.join(word_pys))

        all_pys.append(sentence_pys)

    return all_pys


@task
def join_names_present_in_translations(segmentations, pinyins, translations, global_known_names=[], fixed_translations={}):
    global_known_name_hzs = [hz for hz, py in global_known_names]
    global_known_name_hzs_set = set(global_known_name_hzs)

    # These chars have simple translations that may show up spuriously in the target translation
    DISALLOW_HZ = '了啦吧呢啊吗呗嘛呀'
    # These are pinyin/wade-giles that are common words in english or tend to show up in translations
    DISALLOW_SINGLE_PY = [
        'you',
        'a',
        'e',
        'yu',
        'i',
        'to',
        'so',
        'no',
        'me',
        'do',
        'an',
        'ha',
        'ma',
        'she',
        'man',
        'men',
        'he',
        'la',
        # Words, but not very common (or hasn't been a problem yet):
        #'hang',
        #'ran',
        #'tan',
        #'dui',  # DUI
    ]
    TITLES = [
        ('警官', 'post'),
        ('医生', 'post'),
        ('经理', 'post'),
        ('院长', 'post'),
        ('总', 'post'),
        ('长', 'post'),
        ('师', 'post'),
        ('师父', 'post'),
        ('师傅', 'post'),
        ('老', 'pre'),
        ('小', 'pre'),
        ('先生', 'post'),
        ('小姐', 'post'),
        ('女士', 'post'),
        ('副总', 'post'),
        ('姐', 'post'),
        ('姐姐', 'post'),
        ('哥', 'post'),
        ('哥哥', 'post'),
        ('妹', 'post'),
        ('妹妹', 'post'),
        ('弟', 'post'),
        ('弟弟', 'post'),
        ('主管', 'post'),
    ]

    confirmed_names = []

    for j, ((ws_sentence, psos_sentence, ners_sentence, people, compounds), pys_sentence, transls) in enumerate(zip(segmentations, pinyins, translations)):
        transls = [tr.lower() for tr in transls]
        transl_matches = []
        taken_transl = []
        for transl in transls:
            transl_matches.append([])
            taken_transl.append([False] * len(transl))

        for window_size in [5, 4, 3, 2, 1]:
            for i in range(len(ws_sentence) - window_size + 1):
                for remove_titles in [[], TITLES]:  # try both with and without removing titles
                    components = list(ws_sentence[i : i + window_size])
                    empty_components = [len(filter_text_hanzi(c[-1])) == 0 and c[-1] != ' ' for c in components]
                    if True in empty_components:
                        continue

                    full_joined_hz = ''.join([hz for _, _, hz in components])

                    # NOTE: we use all potential pinyins for a character here, because the classification made by pys_sentence is often wrong for names
                    py_options = [
                        cedict_all_possible_pinyins(hz, split=True, no_tone=True, lower=True)
                        for _, _, hz in components
                    ]

                    # Remove the titles from the pinyin that we match agains the translation
                    removed = False

                    component_pys = list(pys_sentence[i : i + window_size])
                    py_prepend, py_append = '', ''
                    for title, pos in remove_titles:
                        if (pos == 'pre' and full_joined_hz.startswith(title)) or (pos == 'post' and full_joined_hz.endswith(title)):
                            for k, ((*comp_indices, hz), py) in enumerate(zip(components, component_pys)):
                                if title in hz:
                                    idx = hz.index(title)
                                    for option in py_options[k]:
                                        del option[idx:idx+len(title)]

                                    py_parts = extract_normalized_pinyin(py)[idx:idx+len(title)]

                                    components[k] = (*comp_indices, hz[:idx]+hz[idx+len(title):])
                                    removed = True
                                    if pos == 'pre':
                                        py_prepend = ''.join(py_parts)
                                    elif pos == 'post':
                                        py_append = ''.join(py_parts)

                    joined_hz = ''.join([hz for _, _, hz in components])  # now without titles

                    if len(joined_hz) > 1 and joined_hz in CEDICT.v and not is_name_according_to_cedict(joined_hz, None, strict=False):
                        # To avoid e.g. 师傅 being treated as a name, when "shifu" appears in translation, ignore
                        # longer words if they're in CEDICT but is not a name according to it
                        continue

                    if len(filter_text_hanzi(full_joined_hz)) != len(full_joined_hz):
                        # Includes some non-hanzi, so skip
                        continue

                    if len(set(list(DISALLOW_HZ)) & set(components)) > 0:
                        continue

                    joined_idx_start = min([idx for idx, _, _ in components])
                    joined_idx_end = max([idx for _, idx, _ in components])

                    def _combine_options(opts):
                        return '(' + '|'.join(opts) + ')'

                    # Platten the options so that we have an options list for each syllable
                    final_py_options = []
                    for idx_py_options in py_options:
                        for idx in range(len(idx_py_options[0])):  # all options should have the same length
                            idx_options = []
                            #print(idx_py_options)
                            for option_pys in idx_py_options:
                                idx_options.append(option_pys[idx])
                                # Add the Wade-Giles variants as well
                                idx_options += pinyin_wade_giles_conversion_table.get(option_pys[idx], ['[UNK]'])
                            final_py_options.append(list(set(idx_options)))

                    # Combined regex for pinyin and Wade Giles, because sometime they're mixed,
                    # like "Long Kodo", where "Long" should be "Lung" if the whole name was Wade Giles as "Kodo" suggests.
                    pinyin_and_wade_giles_regex = (
                        '([^a-zA-Z]|^)' +
                        '[ \-\']*'.join(
                            _combine_options(options)
                            for options in final_py_options
                        ) +
                        '([^a-zA-Z]|$)'
                    )

                    for transl_idx, transl in enumerate(transls):
                        match = re.search(pinyin_and_wade_giles_regex, transl)
                        if match is not None and match.groups():
                            group_indices = []
                            idx = match.span()[0]
                            for group in match.groups():
                                group_indices.append((idx, idx+len(group)))
                                idx += len(group)

                            py_groups = [(g, indices) for g, indices in zip(match.groups(), group_indices) if re.search('[a-zA-Z]', g) is not None]
                            py_indices = [i for g, i in py_groups]
                            py_groups = [g for g, i in py_groups]
                            if len(py_groups) == 0:
                                continue
                            if len(set(py_groups) & set(DISALLOW_SINGLE_PY)) == len(py_groups):
                                # All syllables are disallowed, so skip
                                continue

                            # Construct the pinyin of the name based on what matched the translation
                            joined_py = []
                            for hz, py in zip(joined_hz, py_groups):
                                try_pys = []
                                if py in PINYIN_SYLLABLES:
                                    try_pys.append(py)

                                if py in WADE_GILES_SYLLABLES:
                                    try_pys += wade_giles_pinyin_conversion_table[py]

                                # Now we need to pick the tone, so get the highest frequency tone for this syllable and word
                                cedict_py = None
                                for try_py in try_pys:
                                    cedict_py = cedict_max_freq_pinyin(hz, match_py_syllable=try_py)
                                    if cedict_py is not None:
                                        # Pick the first that has matching cedict entry
                                        break

                                if cedict_py == None:
                                    breakpoint()
                                    raise Exception()

                                joined_py.append(cedict_py)

                            joined_py = (py_prepend + ''.join(joined_py) + py_append).capitalize()
                            transl_idx_start = py_indices[0][0]
                            transl_idx_end = py_indices[-1][1]
                            transl_matches[transl_idx].append((
                                full_joined_hz, joined_py, window_size,
                                joined_idx_start, joined_idx_end, i,
                                transl_idx_start, transl_idx_end
                            ))
                        elif full_joined_hz in global_known_name_hzs_set:
                            joined_py = global_known_names[global_known_name_hzs.index(full_joined_hz)][1]
                            transl_matches[transl_idx].append((full_joined_hz, joined_py, window_size, joined_idx_start, joined_idx_end, i, None, None))
                        elif full_joined_hz in fixed_translations:
                            joined_py = ''.join(component_pys)
                            transl_matches[transl_idx].append((full_joined_hz, joined_py, window_size, joined_idx_start, joined_idx_end, i, None, None))

        for transl_idx, matches in enumerate(transl_matches):
            matches = list(sorted(matches, key=lambda x: (-len(x[0]), -get_difficulty(x[0], x[1]))))
            non_conflicting_matches = []
            for match in matches:
                _, _, _, hz_idx_start, hz_idx_end, *_, transl_idx_start, transl_idx_end = match
                was_global_name_match = transl_idx_end is None

                if not was_global_name_match and True in taken_transl[transl_idx][transl_idx_start:transl_idx_end]:
                    continue

                non_conflicting_matches.append(match)
                if not was_global_name_match:
                    taken_transl[transl_idx][transl_idx_start:transl_idx_end] = [True] * (transl_idx_end - transl_idx_start)

            transl_matches[transl_idx] = non_conflicting_matches

        matches = sum(transl_matches, [])
        matches = list(sorted(matches, key=lambda x: (-len(x[0]), -get_difficulty(x[0], x[1]))))
        full_sentence_hz = ''.join([ws[-1] for ws in ws_sentence])
        taken_chars = [False] * len(full_sentence_hz)
        non_conflicting_matches = []
        for match in matches:
            _, _, _, start_idx, end_idx, _, transl_idx_start, transl_idx_end = match
            if True in taken_chars[start_idx:end_idx]:
                continue
            taken_chars[start_idx:end_idx] = [True] * (end_idx - start_idx)
            non_conflicting_matches.append(match)

        non_conflicting_matches = list(sorted(non_conflicting_matches, key=lambda x: x[3]))  # sort by starting idx
        last_idx = 0
        new_ws_sentence, new_pos_sentence, new_pys_sentence = [], [], []
        component_idx_start, component_idx_end = 0, 0
        for match in non_conflicting_matches:
            joined_hz, joined_py, window_size, joined_idx_start, joined_idx_end, component_idx_start, *_ = match
            component_idx_end = component_idx_start + window_size

            was_global_name_match = match[-1] is None

            if not was_global_name_match:
                # We only want to add names to confirmed_names if it's not a dictionary word, and it's not super easy
                confirmed = False
                if joined_hz in CEDICT.v:
                    if is_name_according_to_cedict(joined_hz, None, strict=False) and get_difficulty(joined_hz, None) > 0.7:
                        confirmed_names.append((joined_hz, joined_py))
                        confirmed = True
                else:
                    confirmed_names.append((joined_hz, joined_py))
                    confirmed = True

                print(f'Joining name (confirmed={confirmed}): {joined_hz} {joined_py} {transls}, {" ".join(ws[-1] for ws in ws_sentence)}, {window_size} {i} {j}')
            else:
                print(f'Joining unconfirmed name: {joined_hz} {joined_py} {" ".join(ws[-1] for ws in ws_sentence)}, {window_size} {i} {j}')

            new_ws_sentence += ws_sentence[last_idx:component_idx_start] + [(joined_idx_start, joined_idx_end, joined_hz)]
            new_pos_sentence += psos_sentence[last_idx:component_idx_start] + ['']
            new_pys_sentence += pys_sentence[last_idx:component_idx_start] + [joined_py]

            people.append((joined_hz, joined_py))
            compounds.append(joined_hz)

            last_idx = component_idx_end

        # Add the remainder
        new_ws_sentence += ws_sentence[component_idx_end:]
        new_pos_sentence += psos_sentence[component_idx_end:]
        new_pys_sentence += pys_sentence[component_idx_end:]

        segmentations[j] = (new_ws_sentence, new_pos_sentence, ners_sentence, people, compounds)
        pinyins[j] = new_pys_sentence

    return segmentations, pinyins, confirmed_names


@task
def _seg_single(hz):
    global ws_driver
    if ws_driver is None:
        ws_driver = CkipWordSegmenter(level=3, device=0)
    return ws_driver([hz])


@batch(_seg_single)
def _seg_batch(hzs_trad):
    global ws_driver
    if ws_driver is None:
        ws_driver = CkipWordSegmenter(level=3, device=0)
    return ws_driver(hzs_trad, batch_size=16)  # default of 256 was too much memory for my GPU


@task
def _pos_single(seg):
    global pos_driver
    if pos_driver is None:
        pos_driver = CkipPosTagger(level=3, device=0)
    return pos_driver([seg])


@batch(_pos_single)
def _pos_batch(segs):
    global pos_driver
    if pos_driver is None:
        pos_driver = CkipPosTagger(level=3, device=0)
    return pos_driver(segs, batch_size=16)


@task
def _ners_single(hz):
    global ner_driver
    if ner_driver is None:
        ner_driver = CkipNerChunker(level=3, device=0)
    return ner_driver([hz])


@batch(_ners_single)
def _ners_batch(hzs):
    global ner_driver
    if ner_driver is None:
        ner_driver = CkipNerChunker(level=3, device=0)
    return ner_driver(hzs, batch_size=16)

BLACKLIST = {
    '我去', '得很', '这不', '不想', '有了', '一对', '可心', '不得', '好走', '喝茶', '都会', '把门', '小的', '个人',
}

@task
def segment_sentence(hz, join_compound_words=True):
    raise NotImplementedError
    return 'segments'


MIDDLE_CHARS = [
    '了', # 毕了业, 结了婚
    '得', # 挺得住
    '点', # 出点钱
    '过', # 出过国
    '不', # 考不上
    '的', '地', '一点', '一点儿', '点儿', '完', '一些', '些',
    # 打你耳光
    #'我', '我的', '我们', '我们的', '你', '您', '你们', '你的', '你们的', '他',
    #'他的', '他们', '他们的', '她', '她的', '她们', '她们的', '它', '它的',
    #'它们', '它们的'
]


@batch(segment_sentence)
def segment_sentences(hzs: List[str], join_compound_words=True):
    # Model expects traditional characters. Seems to work fine without, but to be safe we convert it:
    hzs_trad = [HanziConv.toTraditional(hz) for hz in hzs]
    with Eval():
        ws_trad = _seg_batch(hzs_trad)

    with Eval():
        psos = _pos_batch(ws_trad)
        sentence_ners_trad = _ners_batch(hzs_trad)

    # Convert back to simplified, and split out any spaces to their own segments (the segmentation has these errors)
    ws = []
    for ws_sentence in ws_trad:
        wss = []
        for c in ws_sentence:
            if c == ' ':
                wss.append(c)
                continue

            c = HanziConv.toSimplified(c)
            c = [' ' if p == '' else p for p in c.split(' ')]
            wss += c

        ws.append(wss)

    sentence_ners = []
    for ners in sentence_ners_trad:
        sentence_ners.append([(HanziConv.toSimplified(n.word), n.ner) for n in ners])

    all_people, all_sentence_people = [], []
    for ners in sentence_ners:
        ner_people = []
        for n in ners:
            if n[1] != 'PERSON':
                continue
            if n[0] in CEDICT.v:
                if not is_name_according_to_cedict(n[0], None, strict=True):
                    print('NER', n, ' in CEDICT but not a name, skipping')
                    continue
            ner_people.append((n[0], None))
        all_sentence_people.append(ner_people)
        all_people += ner_people

    all_people = set(all_people)

    # Combine words if in cedict
    all_compounds = []
    for j, (ws_sentence, psos_sentence) in enumerate(zip(ws, psos)):
        sentence_compounds = []

        new_ws_sentence = [ws for ws in ws_sentence]
        new_pos_sentence = [pos for pos in psos_sentence]

        # The transformer segmentation often makes the mistake to join 了 with the next word, e.g 了别 and 了明.
        # In this case (if the compound is not in cedict), split them into two. The second part could be merged with something
        # that comes later
        for i, (hz, pos) in enumerate(zip(new_ws_sentence, new_pos_sentence)):
            if len(hz) > 1 and hz[0] == '了' and hz not in CEDICT.v:
                new_ws_sentence = new_ws_sentence[:i] + ['了', hz[1:]] + new_ws_sentence[i+1:]
                new_pos_sentence = new_pos_sentence[:i] + ['unknown', 'unknown'] + new_pos_sentence[i+1:]

        found_match = True
        while found_match:
            found_match = False

            # Join names
            window_size = 2
            for i in range(len(new_ws_sentence) - window_size + 1):
                components = new_ws_sentence[i : i + window_size]
                if '' in [filter_text_hanzi(c) for c in components]:
                    continue

                joined_hz = ''.join(components)
                taken = ['']*len(joined_hz)
                for name, name_py in all_people:
                    if name in joined_hz:
                        found_name = name
                        found_name_idx = joined_hz.index(name)
                        taken[found_name_idx:found_name_idx+len(found_name)] = list(found_name)

                # Check that name hits both components
                hit_first = False
                start_idx = None
                for k, taken_char in enumerate(taken[:len(components[0])]):
                    if len(taken_char) > 0:
                        hit_first = True
                        start_idx = k
                        break
                hit_second = False
                end_idx = None
                for k, taken_char in enumerate(taken[len(components[0]):]):
                    if len(taken_char) > 0:
                        hit_second = True
                        end_idx = len(components[0]) + k + 1

                if not hit_first or not hit_second or (end_idx - start_idx) > 3:
                    # Names have to touch both components, but not be longer than 3 characters, otherwise it would join stuff like "明哲明成"
                    continue

                component_before = joined_hz[:start_idx]
                component_after = joined_hz[end_idx:]
                new_components = [joined_hz[start_idx:end_idx]]
                if len(component_before) > 0:
                    new_components = [component_before] + new_components
                if len(component_after) > 0:
                    new_components = new_components + [component_after]

                new_ws_sentence = new_ws_sentence[:i] + new_components + new_ws_sentence[i + window_size :]
                new_pos_sentence = new_pos_sentence[:i] + ['joined_name']*window_size + new_pos_sentence[i + window_size :]
                sentence_compounds.append((joined_hz, None))
                found_match = True
                break

        found_match = True
        while found_match:
            found_match = False
            do_not_join = [False]*len(new_ws_sentence)

            for window_size in [7, 6, 5, 4, 3, 2]:
                best_i, best_hz, best_check_hz, best_difficulty = None, None, None, -1

                for i in range(len(new_ws_sentence) - window_size + 1):
                    components = new_ws_sentence[i : i + window_size]

                    joined_hz = ''.join(components)
                    if re.match('^越[\u4e00-\u9fff]+越[\u4e00-\u9fff]+$', joined_hz) is not None:
                        # Had a case where 越战 (Vietnam war) was joined, but it was part of this pattern
                        do_not_join[i : i + window_size] = [True] * window_size

                    if True in do_not_join[i : i + window_size]:
                        continue

                    check_hz = joined_hz
                    # Special cases for e.g.
                    # * split verbs with le5 毕了业 and 结了婚
                    # * 挺得住
                    # * 出点钱
                    # * 出过国
                    for middle_char in MIDDLE_CHARS:
                        pre = ''.join(components[:2])
                        post = ''.join(components[1:])
                        post_post = new_ws_sentence[i+window_size+1] if len(new_ws_sentence) > i + window_size + 1 else None
                        if (
                            window_size == 3 and
                            joined_hz not in CEDICT.v and
                            components[1] == middle_char and
                            middle_char != post_post and # needed this for e.g. (好了好）了
                            pre not in CEDICT.v and
                            post not in CEDICT.v and
                            (components[0] + components[2]) in CEDICT.v

                        ):
                            check_hz = components[0] + components[2]
                            break

                    # Special cases for e.g. 对不对
                    if (
                        window_size == 3 and
                        components[0] == components[2] and
                        components[1] == '不'
                    ):
                        check_hz = components[0]
                        break

                    force_join = False
                    if window_size in [2, 3] and ''.join(components[1:]) in ['不了', '不起', '不上', '不下', '不着', '不清']:
                        force_join = True
                        check_hz = None

                    # Match numbers and ge4. NOTE: allow a single character afterwards, for cases where 个人 is a single component
                    joined_with_divider = '|'.join(components)
                    if re.match('^[一二三四五六七八九十两百千万\|]+(个[\u4e00-\u9fff]?)?$', joined_with_divider) is not None:
                        force_join = True
                        check_hz = None

                    if is_name_according_to_cedict(check_hz, None, strict=True):
                        has_difficult_char = False
                        for char in check_hz:
                            has_difficult_char |= get_difficulty(char, None) > 0.2

                        if not has_difficult_char:
                            continue

                    if force_join or (check_hz in CEDICT.v and check_hz not in BLACKLIST):
                        found_match = True
                        difficulty = get_difficulty(joined_hz)
                        if difficulty > best_difficulty:
                            best_i = i
                            best_hz = joined_hz
                            best_check_hz = check_hz
                            best_difficulty = difficulty

                if best_i is not None:
                    new_ws_sentence = new_ws_sentence[:best_i] + [best_hz] + new_ws_sentence[best_i + window_size :]
                    new_pos_sentence = new_pos_sentence[:best_i] + ['cedict'] + new_pos_sentence[best_i + window_size :]
                    sentence_compounds.append((best_hz, best_check_hz))
                    print('Components:', best_hz)

                if found_match:
                    break

        if join_compound_words:
            ws[j] = new_ws_sentence
            psos[j] = new_pos_sentence

        all_compounds.append(sentence_compounds)

    final_ws = []
    for hz, ws_sentence in zip(hzs, ws):
        final_ws_sentence = []
        next_idx = 0
        for w in ws_sentence:
            idx_start = next_idx
            idx_end = next_idx + len(w)
            word_simplified = hz[idx_start:idx_end]
            final_ws_sentence.append((next_idx, next_idx+len(w), word_simplified))
            next_idx += len(w)
        final_ws.append(final_ws_sentence)

    return list(zip(final_ws, psos, sentence_ners, all_sentence_people, all_compounds))
