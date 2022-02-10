"""
Block                                   Range       Comment
CJK Unified Ideographs                  4E00-9FFF   Common
CJK Unified Ideographs Extension A      3400-4DBF   Rare
CJK Unified Ideographs Extension B      20000-2A6DF Rare, historic
CJK Unified Ideographs Extension C      2A700–2B73F Rare, historic
CJK Unified Ideographs Extension D      2B740–2B81F Uncommon, some in current use
CJK Unified Ideographs Extension E      2B820–2CEAF Rare, historic
CJK Compatibility Ideographs            F900-FAFF   Duplicates, unifiable variants, corporate characters
CJK Compatibility Ideographs Supplement 2F800-2FA1F Unifiable variants
"""
import os
import re
import sys
import regex
from wrapped_json import json
import math
import numpy as np
from typing import *
from collections import defaultdict
from levenshtein import weighted_levenshtein, OpType
from pinyin import syllable_diacritial_to_number, normalize_pinyin, extract_normalized_pinyin

from merkl import task, FileRef, Future

import jieba_fast as jieba

Cedict = Dict[str, Tuple[str, List[Tuple[str, str, str]], List[Any]]]

def is_hanzi(char: str) -> bool:
    ranges = [('\u4E00', '\u9FFF'), ('\u3400', '\u4DBF'), ('\uF900', '\uFAFF')]
    for start, end in ranges:
        if ord(char) >= ord(start) and ord(char) <= ord(end):
            return True
    return False


def filter_text_hanzi(text: str) -> str:
    return ''.join(char for char in text if is_hanzi(char))


def get_hanzi_ranges(text: str) -> List[Tuple[int, int]]:
    """ Returns a list of pure Hanzi strings in `text`, as a tuple of start and end index """
    ranges = []
    start_idx = None
    for i, c in enumerate(text):
        char_is_hanzi = is_hanzi(c)
        if start_idx is None and char_is_hanzi:
            start_idx = i
        elif start_idx is not None and not char_is_hanzi:
            ranges.append((start_idx, i + 1))
            start_idx = None

    if start_idx is not None:
        ranges.append((start_idx, len(text)))

    return ranges


UNIHAN_CHAR_READINGS: Dict[str, List[Tuple[str, int]]] = {}
HSK: Dict[int, Set[str]] = {}
JIEBA_POS_FREQ: Dict[str, Tuple[str, int]] = {}

def load_hsk_unihan_jieba():
    # Read HSK level words, Unihan readings and jieba dict. These are not directly
    # imported to the database, but are used by other functions
    for lvl in range(1, 7):
        hsk_file = f'data/git/hsk/HSK{lvl}.txt'
        lvl_words = set(open(hsk_file, 'r', encoding='utf-8').read().splitlines())
        # Split up words and add individual characters
        chars: Set[str] = set()
        for word in lvl_words:
            chars = chars | set(word)
        HSK[lvl] = lvl_words | chars

    with open('data/git/Unihan_Readings.txt') as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            char, field, data = line.strip().split('\t')
            if field != 'kHanyuPinlu':
                continue
            readings = data.split(' ')
            reading_and_freq = [re.split('[\(\)]', r) for r in readings]
            # Convert the char from a string on the form "U+3495" to
            # the actual unicode character in a utf string
            char = chr(int(char[2:], 16))
            UNIHAN_CHAR_READINGS[char] = [(syllable_diacritial_to_number(r[0]), int(r[1])) for r in reading_and_freq]

    with open('data/git/jieba_dict.txt') as f:
        for line in f:
            hz, freq, pos = line.strip().split(' ')
            JIEBA_POS_FREQ[hz] = (pos, int(freq))


@task(serializer=json, deps=[FileRef('data/git/cedict_ts.u8'), FileRef('data/git/cedict_ignore.txt'), FileRef('data/git/cedict_freq_override.txt')])
def make_cedict(freqs=None) -> Cedict:
    load_hsk_unihan_jieba()
    cedict_ignore = set()
    with open('data/git/cedict_ignore.txt') as f:
        for line in f:
            if line.startswith('#'):
                continue
            line = line.strip()
            line = line[:line.index(']')+1]
            cedict_ignore.add(line)

    if freqs is not None:
        cedict_freq_override = set()
        with open('data/git/cedict_freq_override.txt') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                line = line.strip()
                line = line[:line.index(']')+1]
                cedict_freq_override.add(line)

        readings_freq_all, readings_freq_single = freqs

    cedict = defaultdict(list)
    with open('data/git/cedict_ts.u8', 'r', encoding="utf-8") as f:
        total_freqs = 0
        for i, line in enumerate(f):
            tr_sm_py = line[:line.index(']')+1] if ']' in line else None
            if line.startswith('#') or tr_sm_py in cedict_ignore:
                continue

            m = re.match(r"(\S*) (\S*) \[(.*)\] \/(.*)\/", line)
            if m:
                tr, sm, py, transl = m.groups()
                transl_split = transl.split('/')
                py = normalize_pinyin(py.replace(' ', ''))
            else:
                continue

            transl = '/'.join(
                [
                    t for t in transl_split
                ]  # fmt: off
            )

            hz = sm

            if freqs is not None:
                # Now we scale the jieba frequency by the proportion of the frequency
                # for this pinyin as found in the ChinesePod dataset. First we check
                # if there is data for single-characters (when jieba segmented it as
                # a single character), or if that fails use the frequency seen in compounds
                # NOTE: we do this because jieba list doens't have frequencies for the different pinyin readings of a word
                _, freq = JIEBA_POS_FREQ.get(sm, (None, None))
                freq = 0 if tr_sm_py in cedict_freq_override else freq
                single_freqs = readings_freq_single.get(hz, None)
                all_freqs = readings_freq_all.get(hz, None)

                #if freq is not None:
                    #log_freq = math.log(max(1, freq))
                    #print(f'{hz} - {py}: log(freq): ', log_freq)

                if freq and (single_freqs or all_freqs):
                    def _get_scaled_freq(freqs):
                        if not freqs:
                            return 0
                        total_num = 0
                        for _, exerpts in freqs.items():
                            total_num += len(exerpts)
                        if py.lower() in freqs:
                            chinespod_freq = len(freqs[py.lower()])
                            return int(freq * chinespod_freq / total_num)
                        else:
                            return 0

                    if single_freqs:
                        freq = _get_scaled_freq(single_freqs)
                        #print(f'{hz} - {py}: using single freq: {freq}')
                    elif all_freqs:
                        freq = _get_scaled_freq(all_freqs)
                        #print(f'{hz} - {py}: using all freq: {freq}')

                difficulty = None
                if freq:
                    # Take the log to make the difficulty scale linear
                    # Cut off below 1000 and above 100000 examples
                    difficulty = 1.0 - min(max(np.log(freq) - np.log(1000), 0) / (np.log(100000) - np.log(1000)), 1.0)
                    total_freqs += freq
            else:
                freq, difficulty = None, None

            cedict[sm].append((tr, py, transl, freq, difficulty))

    # Find compounds with jieba
    # NOTE: also normalize the freqs to probabilites
    compound_parts = {}
    for sm, entries in cedict.items():
        # search mode will produce compounds and their parts
        tokens = list(jieba.tokenize(sm, mode='search'))
        parts = [t for t in tokens if t[2] - t[1] < len(sm)]
        compound_parts[sm] = parts

        for i, entry in enumerate(entries):
            freq = entry[-2]
            if freq is None:
                continue

            entries[i] = (*entry[:-2], freq / total_freqs, *entry[-1:])
            print(freq, entries[i][-2])

    # Join multiple sound characters (多音字)
    cedict_dict = {sm: (sm, entries, compound_parts[sm]) for sm, entries in cedict.items()}
    return cedict_dict


def _hz_py_subst_cost(hz: str, py: str, *args) -> float:
    if hz not in CEDICT.v:
        return 1.0
    same_syllable = False
    for entry in CEDICT.v[hz][1]:
        if entry[1].lower() == py.lower():
            return 0.0
        # If syllables without tone number match, cost = 0.5
        if entry[1][:-1] == py.lower()[:-1]:
            same_syllable = True

    # NOTE: penalty of 99 to make it cost more than deletion. We prefer
    # to remove the correnspondence here rather than get it wrong
    return 0.5 if same_syllable else 999.0


def align_hanzi_and_pinyin(hanzi: str, pys: List[str]) -> List[Optional[int]]:
    _, ops = weighted_levenshtein(hanzi, pys, _hz_py_subst_cost, return_ops=True)

    hanzi_pinyin_indices: List[Optional[int]] = []
    for i in range(len(hanzi)):
        hanzi_pinyin_indices.append(None)  # have to do this rather to shut up mymy...

    for op in ops:
        if op.type == OpType.SUBSTITUTE:
            hanzi_pinyin_indices[op.from_idx] = op.to_idx

    return hanzi_pinyin_indices


def is_mw_according_to_cedict(hz, py):
    if hz not in CEDICT.v:
        return False

    entries = CEDICT.v.get(hz)[1]
    for _, entry_py, transl, _, _ in entries:
        if entry_py != py and entry_py != py.lower():
            continue
        transls = transl.split('/')
        for tr in transls:
            if tr.startswith('classifier '):
                return True

    return False


def get_difficulty(hz, py=None):
    if hz not in CEDICT.v:
        return 1.0

    entries = CEDICT.v.get(hz)[1]
    min_difficulty = 1
    for _, entry_py, transl, _, difficulty in entries:
        if py != None and entry_py != py and entry_py != py.lower():
            continue
        if difficulty is not None:
            if min_difficulty is None:
                min_difficulty = difficulty
            else:
                min_difficulty = min(difficulty, min_difficulty)

    return min_difficulty


def is_name_according_to_cedict(hz, py, strict=True):
    if hz not in CEDICT.v:
        return False

    entries = CEDICT.v.get(hz)[1]
    for _, entry_py, transl, _, _ in entries:
        if py != None and entry_py != py and entry_py != py.lower():
            continue

        if entry_py[0].isupper():
            return True

        transls = transl.split('/')
        for tr in transls:
            # NOTE: Some translation expressions are capitalized, e.g. "How
            # your getting by?", often with punctuation mark after, so filter
            # out those

            if (
                tr.startswith('CL') or
                tr.startswith('Kangxi') or
                tr.endswith('?') or
                tr.endswith('!') or
                '...' in tr or
                tr.startswith('OK') or
                tr.startswith('I')
            ):
                continue

            if (
                tr[0].isupper() or '(name)' in tr or
                'old name' in tr or
                tr.startswith('surname ') or
                '(surname)' in tr or
                '(used in names)' in tr
            ):
                return True

    return False


def clean_cedict_translation(tr, hz=None, py=None, split_or=True, remove_parens=True):
    if tr == '!':
        return []

    if py is not None and hz is not None:
        if (
            not is_name_according_to_cedict(hz, py) and
            tr[0].isupper() and
            tr not in ['I', 'OK'] and
            not tr.startswith('CL') and
            not tr.startswith('I ') and
            not tr.startswith("I'") and
            not tr.startswith("OK") and
            not tr.startswith('Kangxi') and
            not tr.upper() == tr  # if all letters are uppercase then it's probably an acronym
        ):
            tr = tr[0].lower() + tr[1:]

    if py is not None:
        py_regex = (
            '( |^)' +
            ' ?'.join(re.sub('[1-5]', '', py) for py in extract_normalized_pinyin(py)) +
            '( |$)'
        )

        if re.search(py_regex, tr) is not None:
            # It's probably a name like a district, province etc
            return []

    def _filter_translation(tr):
        return (
            '...' in tr or
            #' sth' in tr or
            #' sb' in tr or
            '(archaic)' in tr or
            'euphemism ' in tr or
            '(euphemism' in tr or
            'Kangxi radical' in tr or
            re.match('adjective.+', tr) is not None or  # adjective plus space comma
            tr.endswith('-') or
            tr.startswith('-') or
            tr.startswith('surname ') or
            'particle ' in tr or
            tr.startswith('classifier for ') or
            tr.startswith('classifier: ') or
            tr.startswith('see also ') or
            tr.startswith('variant of') or
            ('pr.' in tr and '[' in tr) or
            (tr.startswith('see ') and '[' in tr) or
            (tr.startswith('old variant ') and '[' in tr) or
            (tr.startswith('variant ') and '[' in tr) or
            (tr.startswith('also ') and '[' in tr) or
            (tr.startswith('used in ') and '[' in tr)
        )

    if _filter_translation(tr):
        return []

    if remove_parens:
        tr = re.sub('\(.*\)', '', tr)
    else:
        tr = tr.replace('(', '').replace(')', '')

    tr = re.sub('-', ' ', tr)  # replace hyphens by space, e.g. "narrow-minded" -> "narrow minded", so we can match individual words
    tr = tr.strip()
    lstrip = ['to ', 'the ', 'be ', 'to be ', "one's ", 'a ', 'an ']
    for s in lstrip:
        if tr.startswith(s):
            tr = tr[len(s):]
    tr.replace('fig. ', '')
    tr.replace('lit. ', '')
    tr = tr.replace('?', '')
    tr = tr.replace("'", " '")

    m = regex.match('abbr. for ([A-Z][a-z]+ ?)+', tr)
    if m is not None:
        tr = [n.strip() for n in m.captures(1) if n[0].isupper() and 'Province' not in n]
    else:
        if split_or:
            tr = re.split(';| or ', tr)
        else:
            tr = re.split(';', tr)

    transls_out = []
    for tr_split in tr:
        if len(filter_text_hanzi(tr_split)) > 0:
            continue

        tr_split = tr_split.strip()
        if _filter_translation(tr_split) or tr_split == '':
            continue

        tr_split = tr_split.replace("  ", " ")  # replace double spaces
        transls_out.append(tr_split)

    return transls_out


CEDICT = Future.from_file('data/remote/private/cedict_with_freqs.json', raise_file_not_found=False)
if CEDICT is None:
    CEDICT = make_cedict()


@task
def get_idioms():
    idioms = {}
    for hz, (_, entries, _) in CEDICT.v.items():
        entry_cleaned_transls = []
        entry_transls = []
        added_idiom = False
        for (tr, py, transl, _, _) in entries:
            transls = [t for t in transl.split('/') if t != '']
            entry_transls += transls
            cleaned_transls = sum([clean_cedict_translation(tr, py=py) for tr in transls], [])
            entry_cleaned_transls += cleaned_transls

            for tr in transls:
                if ';' in tr:
                    tr = tr.split(';')[0].strip()

                if '(idiom)' in tr:
                    tr = tr.replace('(idiom)', '').strip()
                    print(f'Idiom: {hz} {tr}')
                    idioms[hz] = tr
                    added_idiom = True
                    break

        if not added_idiom and len(entries) == 1 and len(entry_transls) == 1 and len(entry_cleaned_transls) > 0 and len(hz) >= 3:
            print(f'Not Idiom but adding: {hz} {entry_cleaned_transls}')
            idioms[hz] = entry_cleaned_transls[0]

    return idioms
