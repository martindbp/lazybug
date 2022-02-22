import re
from copy import deepcopy
from collections import defaultdict
from wrapped_json import json
import itertools
import numpy as np
from iteration_utilities import unique_everseen
from sentence_transformers import SentenceTransformer
from han import filter_text_hanzi, CEDICT, clean_cedict_translation, is_name_according_to_cedict
from misc import get_punctuation
from pinyin import extract_normalized_pinyin
from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F
from wordfreq import word_frequency
from word_forms.word_forms import get_word_forms
from data.git import pinyin_classifiers

from merkl import task, batch, Eval

model = None

NEVER_SPLIT = [
    '个',
    '现在',
    '还没',
    '大哥',
    '小妹',
    '不是',
    #'到',
    '识',
    '子',
]

SKIP = [
    '的',
    '啊', 
    '吗',
    '呗',
    '嘛', 
    '呀',
    '了',
    '啦',
    '吧',
    #'呢',
    '着',
    '得',
]

DISALLOW_MWS = [
    '盒', '双', '杯', '平', '把', '堆', '包', '卷', '桶', '束', '次', '阵', '刻', '番', '份', '片', '块', '口',
    '碗', '盘', '滴', '壶', '罐', '些', '种', '群', '众', '帮', '班', '排', '队', '串', '打', '叠', '秒', '分', '天',
    '日', '周', '年', '代', '斤', '吨', '磅', '坪', '块', '毛', '笔', '寸', '尺', '里', '升', '斗', '度', '声', '岁',
    '平方公里', '瓶', '伙',
    '出', # (classifier for plays or chapters of classical novels)/
]

ALLOW_EMPTY = [
    '把', '来', '过', '地', '到', '先', '呢', '可',
]


@task
def embed_string(s):
    return model.encode([s])


@batch(embed_string)
def embed_strings(s):
    embeddings = model.encode(s)
    return [embeddings[i, :] for i in range(len(s))]


def get_all_word_forms(word, pos=None):
    MANUAL_WORD_FORM_GROUPS = [
        {'you', 'your', "your's", "you"},
        {'I', 'me', "mine", "my", "I"},
        {'he', 'his', "he's", 'him'},
        {'she', 'her', "her's", "she"},
        {'we', 'our', "our's", "we"},
    ]
    MANUAL_GROUP_WORDS = set(sum([list(group) for group in MANUAL_WORD_FORM_GROUPS], []))

    if word in MANUAL_GROUP_WORDS:
        for group in MANUAL_WORD_FORM_GROUPS:
            if word in group:
                return group

    forms = get_word_forms(word, similarity_threshold=0.0)
    adjective_forms = set()

    # For some reason e.g. "clearer" is missing for "clear"
    for form in forms['a']:
        if form[-1].lower() in ['a', 'e', 'i', 'u', 'o', 'y']:
            form = form[-1]
        adjective_forms |= {form+'er', form+'est', form + 'ly'}

    forms = forms['v'] | forms['a'] | forms['n'] | forms['r'] | adjective_forms
    plural_forms = set()
    # Add e.g. thieves for thiefs
    for form in forms:
        if form.endswith('fs'):
            plural_forms.add(form[:-2] + 'ves')

    forms |= plural_forms

    if 'payed' in forms:
        forms.add('paid')

    return forms


def join(words):
    res = ' '.join(words)
    # Transform e.g. "what 's up" -> "what's up"
    return re.sub("([A-Za-z]) \'", "\\1'", res)


def get_similarity(base_translations, combined_translations, print_iterations=False):
    sentences = [*base_translations, *[join(t for t in transl if t != '') for transl in combined_translations]]

    with Eval():
        embeddings = embed_strings(sentences)
        embeddings = np.stack(embeddings)

    # A*A^T gives cosine similarity
    cosine_similarity = embeddings @ embeddings.T
    cosine_similarity = cosine_similarity[:len(base_translations), len(base_translations):]  # similarity between translations and each option
    cosine_similarity = np.max(cosine_similarity, axis=0)  # take the maximum across translations
    max_idx = np.argmax(cosine_similarity)
    max_similarity = np.max(cosine_similarity)

    if print_iterations:
        for i in range(len(combined_translations)):
            print(combined_translations[i], cosine_similarity[i])

    return max_similarity, max_idx, cosine_similarity


def get_translation_options_cedict(hz, py, deepl, add_empty=True, split_or=True):
    # Returns list of ([option strings], exact_match_only, py)

    options = []
    if deepl not in [None, '', '[UNK]']:
        deepl = re.sub('-', ' ', deepl)
        options.append((deepl.split(' '), False, py))

    if hz in SKIP: # and add_empty:
        options.append(([''], False, py))
        return options

    if hz not in CEDICT.v:
        if len(options) == 0 and add_empty:
            options.append(([''], False, py))
        return options

    entries = CEDICT.v.get(hz)[1]
    #if hz in ALLOW_EMPTY and add_empty:
    if add_empty and deepl not in [None, '', '[UNK]']:
        options.append(([''], False, py))

    for _, entry_py, transl, _, _ in entries:
        # Only check translations for the correct pinyin (if it's one we trained a classifier for)
        if (
            py is not None and
            entry_py.lower() != py.lower() and
            (hz in pinyin_classifiers.__dict__ or hz in pinyin_classifiers.single_readings)
        ):
            continue

        transls = transl.split('/')

        # By convention, anyting after ! is for exact matching only
        rest_is_exact_match_only = False
        for tr in transls:
            if tr == '!':
                rest_is_exact_match_only = True
                options.insert(0, ([''], False, entry_py))
                continue

            # We include options with and without parenthesised text, e.g. 九 -> "(long) time", we want
            # both "long", and "long time" options
            trs = (
                clean_cedict_translation(tr, hz, entry_py, split_or=split_or, remove_parens=True) +
                clean_cedict_translation(tr, hz, entry_py, split_or=split_or, remove_parens=False)
            )

            for tr_split in trs:
                if ' sb' in tr_split or ' sth' in tr_split or " one's" in tr_split:
                    # We want to allow the text before and after to be matched separately
                    split_options = re.split(" sb| sth| one's", tr_split)
                    split_options = [op.strip() for op in split_options if op != '']
                    options.append((split_options, rest_is_exact_match_only, entry_py))
                elif len(tr_split) != 0:
                    options.append((tr_split.split(' '), rest_is_exact_match_only, entry_py))

    if add_empty and len(options) == 0:
        options.append(([''], False, py))

    options = list(unique_everseen(options, key=lambda x: ' '.join(x[0])))
    return options


def _nail_down_options(baseline_words, translation_options, current_option_indices, current_nailed_down_options, current_segmentation_idx, clear_options=True):
    if current_nailed_down_options[current_segmentation_idx]:
        return translation_options, current_nailed_down_options, current_option_indices, False

    # Nail down translation options that exist in the baselines
    current_translation_options = deepcopy(translation_options)
    options = current_translation_options[current_segmentation_idx]

    current_other_active_options = defaultdict(lambda: 0)

    for i in range(len(translation_options)):
        if i == current_segmentation_idx:
            continue

        if current_option_indices[i] < 0:
            continue

        ops, *_ = translation_options[i][current_option_indices[i]]
        for op in ops:
            for op_variation in get_all_word_forms(op):
                current_other_active_options[op_variation.lower()] += 1

    all_option_forms = []
    for i, (option, _, py) in enumerate(options):
        if option == ['']:
            continue
        all_option_forms.append((option, py))
        option_part_forms = [[part] + list(get_all_word_forms(part)) for part in option]
        combinations = list(itertools.islice(itertools.product(*option_part_forms), 10000))
        all_option_forms += [(list(c), py) for c in combinations]

    exact_matches = []
    max_num_words = 0
    # Remove duplicates (need to convert list to tuples
    all_option_forms = list(unique_everseen(all_option_forms, key=lambda x: ' '.join(x[0])))
    for option, py in all_option_forms:
        baseline_text = join(baseline_words)
        all_match = True
        last_match_idx = -1
        for i, split_option in enumerate(option):
            matches = False
            if ' ' in split_option or split_option.startswith("'"):
                # If option contains more than one word or starts with apostrophe, then match against text directly, otherwise
                # word by word
                matches = split_option.lower() in baseline_text
                if matches:
                    match_idx = baseline_text.index(split_option.lower())
            else:
                matches = split_option.lower() in baseline_words
                # The idx is the string idx, so sum up all words before the match:
                if matches:
                    match_idx = len(join(baseline_words[:baseline_words.index(split_option.lower())]))

            if not matches or match_idx < last_match_idx:  # match has to be in the right order
                all_match = False
                break
            last_match_idx = match_idx

        if all_match:
            exact_matches.append((option, py, last_match_idx))
            max_num_words = max(max_num_words, len(option))

    # Keep the options with the max number of matched words
    exact_matches = [(match, *_) for match, *_ in exact_matches if len(match) == max_num_words]
    exact_matches = list(unique_everseen(exact_matches, key=lambda x: ' '.join(x[0]).lower()))

    changed = False
    if len(exact_matches) > 0:
        exclusive_matches = []
        for match, py, match_pos in exact_matches:
            all_exclusive = True
            for op in match:
                num_op_in_baseline = sum([1 for w in baseline_words if w == op.lower()])
                if current_other_active_options[op.lower()] >= num_op_in_baseline and not (op == 'if'):
                    all_exclusive = False

            if all_exclusive:
                exclusive_matches.append((match, py, match_pos))

        # If we have at least one exclusive match, we clear the original options and use just those
        if len(exclusive_matches) > 0:
            if clear_options:
                options.clear()

            # NOTE: we sort by match pos, because if current option is set,
            # it means that it was present in a higher priority baseline, so if we have an exact match we want to pick that
            for match, py, _ in sorted(exclusive_matches, key=lambda x: x[2]):
                options.append((match, True, py))
        else:
            # NOTE: sort by lowest frequency, because we often prefer the rarer
            # (more specific) words. Placing them first in the options means
            # that the similarity improvement of the more common word would
            # have to be greater than a threshold before choosing it.
            for match, py, _ in sorted(exact_matches, key=lambda x: min([word_frequency(w, 'en') for w in x[0]])):
                options.append((match, True, py))

        if len(exclusive_matches) == 1:
            current_nailed_down_options[current_segmentation_idx] = True
            changed = True
        current_option_indices[current_segmentation_idx] = 0

    return current_translation_options, current_nailed_down_options, current_option_indices, changed


def _nail_down_consecutive_options(baseline_text, translation_options, current_option_indices, current_nailed_down_options):
    baseline_text = baseline_text.lower()
    # If the combination of 2-4 options exists in a baseline, then we assign them.
    for sub_length in range(2, 5):
        for start_idx in range(0, len(translation_options) - sub_length):
            range_options = translation_options[start_idx:start_idx + sub_length]
            # Filter out empty options
            range_options = [[(op[0], op[2]) for op in options if op[0] != ['']] for options in range_options]

            for comb in itertools.product(*range_options):
                comb_text = ' '.join([' '.join(c[0]) for c in comb])
                if re.match(f".*([^a-zA-Z]|^){comb_text}([^a-zA-Z]|$).*", baseline_text) is not None:
                    print(f'Combining options: {comb_text}')
                    current_option_indices[start_idx:start_idx + sub_length] = [0]*sub_length
                    translation_options[start_idx:start_idx + sub_length] = [[(c[0], True, c[1])] for c in comb]
                    current_nailed_down_options[start_idx:start_idx + sub_length] = [True] * sub_length

    return translation_options, current_option_indices, current_nailed_down_options


def get_baseline_words(base_translations):
    baseline_words = [
        [w.lower() for w in re.sub('-', ' ', re.sub('\.|,|;|:|\?|\!', '', t.replace("'", " '"))).split(' ')]
        for t in base_translations
    ]
    for baseline in baseline_words:
        for word in baseline:
            if "'" in word:
                for split in word.split("'"):
                    baseline.append(split)

    return baseline_words


def get_options(hzs, base_translations, pys, deepl_translations=None, skip_words=None):
    translation_options = []

    if deepl_translations is None:
        deepl_translations = [None] * len(hzs)
    if skip_words is None:
        skip_words = [False] * len(hzs)

    for i, (hz, py, deepl, skip) in enumerate(zip(hzs, pys, deepl_translations, skip_words)):
        if skip:
            translation_options.append([([''], False, py)])
        else:
            translation_options.append(get_translation_options_cedict(hz, py, deepl))

    current_option_indices = [-1] * len(hzs)
    current_order = list(range(len(current_option_indices)))
    current_nailed_down_options = [False] * len(hzs)

    baselines = get_baseline_words(base_translations)

    # Start nailing down largest words first
    indices_sorted_by_hz_len = sorted(range(len(current_option_indices)), key=lambda i: -len(hzs[i]))

    for baseline_words in baselines:
        changed = True
        while changed:
            changed = False
            for i in indices_sorted_by_hz_len:
                translation_options, current_nailed_down_options, current_option_indices, _changed = _nail_down_options(
                    baseline_words, translation_options, current_option_indices, current_nailed_down_options, i
                )
                changed = changed or _changed

    for i in range(len(current_option_indices)):
        if current_option_indices[i] < 0:
            current_option_indices[i] = 0

    # If we have multiple non-nailed down options, and a deepl option, let's use DeepL. This after realizing that
    # sentence embedding often fails, we should only use it if we have no other option
    for i, options in enumerate(translation_options):
        if current_nailed_down_options[i]:
            continue

        if len(translation_options[i]) > 1 and deepl_translations[i] not in [None, '', '[UNK]']:
            translation_options[i] = translation_options[i][:1]

    return translation_options, current_option_indices, current_nailed_down_options, current_order


@task(ignore_args=['print_iterations'], deps=[CEDICT, clean_cedict_translation])
def get_embedding_word_translations(hzs, pys, alignment_indices, base_translations, skip_words, prevent_split, deepl_translations=None, print_iterations=False):
    orig_pys = list(pys)
    global model
    if model is None:
        model = SentenceTransformer('sentence-transformers/paraphrase-mpnet-base-v2')

    def _get_combined_translation(option_indices, order, options):
        combined_translation = []
        for i in order:
            idx = option_indices[i]
            option = options[i][idx][0]
            combined_translation.append(' '.join(option))

        punctuation = get_punctuation(base_translations[0])
        if punctuation is not None:
            combined_translation.append(punctuation)

        return combined_translation

    def _get_combined_pys(option_indices, order, options):
        combined_pys = []
        for i in order:
            idx = option_indices[i]
            combined_pys.append(options[i][idx][2])

        return combined_pys


    translation_options, current_option_indices, current_nailed_down_options, current_order = get_options(
        hzs, base_translations, pys, deepl_translations, skip_words
    )

    baselines = get_baseline_words(base_translations)

    print('OPTIONS:', translation_options)

    current_translation = _get_combined_translation(current_option_indices, current_order, translation_options)
    print('INITIAL', current_translation)
    best_similarity, *_ = get_similarity(base_translations, [current_translation], print_iterations=print_iterations)

    # NOTE: swap_order not functioning correctly yet
    for operation in ['swap_translation', 'split_word', 'swap_translation']: #, 'swap_order', 'swap_translation']:
        print('OPERATION', operation)
        iterations_since_last_change = 0
        current_segmentation_idx = 0
        while iterations_since_last_change < len(hzs):
            combined_translations = []
            combined_pys = []

            current_translation_options = translation_options

            if operation == 'swap_translation':
                for i, (option, exact_match_only, py) in enumerate(current_translation_options[current_segmentation_idx]):
                    if exact_match_only:
                        combined_translations.append([''])
                        combined_pys.append(None)
                        continue
                    new_option_indices = list(current_option_indices)
                    new_option_indices[current_segmentation_idx] = i
                    combined_translations.append(_get_combined_translation(new_option_indices, current_order, current_translation_options))
                    combined_pys.append(_get_combined_pys(new_option_indices, current_order, current_translation_options))
            elif operation == 'swap_order':
                for swap_with_idx in range(len(current_order)):
                    new_order = list(current_order)
                    new_order[current_segmentation_idx], new_order[swap_with_idx] = new_order[swap_with_idx], new_order[current_segmentation_idx]
                    combined_translations.append(_get_combined_translation(current_option_indices, new_order, current_translation_options))
                    combined_pys = _get_combined_pys(current_option_indices, new_order, current_translation_options)
            elif operation == 'split_word':
                # Add all possible option combinations for the split words (if exists)
                hz = hzs[current_segmentation_idx]
                py = pys[current_segmentation_idx]
                no_split = prevent_split[current_segmentation_idx]
                first_hz, second_hz = None, None
                both_have_translations = False
                for split_idx in range(1, len(hz)):
                    first_hz = hz[:split_idx]
                    second_hz = hz[split_idx:]
                    first_options = get_translation_options_cedict(first_hz, None, None, add_empty=False)
                    second_options = get_translation_options_cedict(second_hz, None, None, add_empty=False)
                    if (
                        len(first_options) > 0 and
                        len(second_options) > 0 and
                        first_hz not in NEVER_SPLIT and
                        second_hz not in NEVER_SPLIT and
                        hz not in NEVER_SPLIT and
                        not no_split and
                        first_hz != second_hz  # don't want to split e.g 妈妈 爸爸
                    ):
                        both_have_translations = True
                        break

                deepl_option = current_translation_options[current_segmentation_idx][0][0]
                cedict_options = [op[0] for op in current_translation_options[current_segmentation_idx][1:]]
                current_option_is_deepl = (
                    current_option_indices[current_segmentation_idx] == 0 and
                    (
                        len(translation_options[current_segmentation_idx]) != 1 or
                        hz not in CEDICT.v
                    )
                    and deepl_option not in cedict_options
                )

                if both_have_translations:
                    # Found a valid split
                    split_pys = extract_normalized_pinyin(py)
                    first_py, second_py = ''.join(split_pys[:split_idx]), ''.join(split_pys[split_idx:])

                    new_translation_options = list(current_translation_options)
                    new_option_indices = list(current_option_indices)
                    new_nailed_down_options = list(current_nailed_down_options)
                    new_order = list(current_order)
                    new_hzs = list(hzs)
                    new_prevent_split = list(prevent_split)

                    new_hzs[current_segmentation_idx:current_segmentation_idx+1] = [first_hz, second_hz]
                    new_translation_options[current_segmentation_idx:current_segmentation_idx+1] = [
                        first_options,
                        second_options,
                    ]
                    new_prevent_split[current_segmentation_idx:current_segmentation_idx+1] = [False, False]
                    new_option_indices[current_segmentation_idx:current_segmentation_idx+1] = [-1, -1]
                    new_nailed_down_options[current_segmentation_idx:current_segmentation_idx+1] = [False, False]

                    # If the compound translation is nailed down, we check the components against its word translation instead of the
                    # full translations
                    check_against = baselines
                    if current_nailed_down_options[current_segmentation_idx] and not current_option_is_deepl:
                        check_against = [translation_options[current_segmentation_idx][0][0]]

                    for baseline_words in check_against:
                        changed = True
                        while changed:
                            changed = False
                            new_translation_options, new_nailed_down_options, new_option_indices, _changed = _nail_down_options(
                                baseline_words, new_translation_options, new_option_indices, new_nailed_down_options, current_segmentation_idx
                            )
                            changed = changed or _changed
                            new_translation_options, new_nailed_down_options, new_option_indices, _changed = _nail_down_options(
                                baseline_words, new_translation_options, new_option_indices, new_nailed_down_options, current_segmentation_idx+1
                            )
                            changed = changed or _changed

                    # Make space for the new split order item by incrementing orders above current
                    for i in range(len(new_order)):
                        if new_order[i] > new_order[current_segmentation_idx]:
                            new_order[i] += 1

                    new_order[current_segmentation_idx:current_segmentation_idx+1] = [new_order[current_segmentation_idx], new_order[current_segmentation_idx] + 1]

                    # Require that at both of the new options are nailed down, this is to reduce false positives
                    # Also, require the options to not be too many, as then there's a high chance that one of them is a simple common word
                    current_first_option = new_translation_options[current_segmentation_idx][new_option_indices[current_segmentation_idx]]
                    current_second_option = new_translation_options[current_segmentation_idx+1][new_option_indices[current_segmentation_idx+1]]
                    current_options_intersection = (
                        set([' '.join(op[0]) for op in new_translation_options[current_segmentation_idx]]) &
                        set([' '.join(op[0]) for op in new_translation_options[current_segmentation_idx+1]])
                    )

                    num_first_options_with_same_py = sum([1 for op in first_options if op[-1] == current_first_option[-1]])
                    num_second_options_with_same_py = sum([1 for op in second_options if op[-1] == current_second_option[-1]])

                    both_nailed_down = (
                        new_nailed_down_options[current_segmentation_idx] and
                        new_nailed_down_options[current_segmentation_idx+1]
                    )
                    if (
                        both_nailed_down and (
                            (
                                current_nailed_down_options[current_segmentation_idx] and
                                #hz not in CEDICT.v and
                                (  # Make sure it covers all the words in the compound translation
                                    len(new_translation_options[current_segmentation_idx][0][0]) +
                                    len(new_translation_options[current_segmentation_idx+1][0][0]) ==
                                    len(current_translation_options[current_segmentation_idx][0][0])
                                )
                            )
                            or
                            (
                                (not current_nailed_down_options[current_segmentation_idx] or current_option_is_deepl) and
                                len(current_options_intersection) == 0 and
                                num_first_options_with_same_py < 10 and
                                num_second_options_with_same_py < 10
                            )
                        )
                    ):
                        # Finally add the new combinations
                        option_idx_combinations = list(itertools.product(
                            list(range(len(new_translation_options[current_segmentation_idx]))),
                            list(range(len(new_translation_options[current_segmentation_idx+1])))
                        ))
                        for option_idx1, option_idx2 in option_idx_combinations:
                            final_option_indices = list(new_option_indices)
                            final_option_indices[current_segmentation_idx:current_segmentation_idx+2] = [option_idx1, option_idx2]
                            combined_translations.append(_get_combined_translation(final_option_indices, new_order, new_translation_options))
                            combined_pys.append(_get_combined_pys(final_option_indices, new_order, new_translation_options))

            if len(combined_translations) > 1 or (len(combined_translations) == 1 and operation == 'split_word'):
                max_similarity, max_idx, cosine_similarity = get_similarity(base_translations, combined_translations, print_iterations=print_iterations)

                is_good_enough = (
                    best_similarity is None or
                    (max_similarity / best_similarity) > 1.00 or
                    operation == 'split_word'
                )

                if combined_translations[max_idx] == ['']:
                    is_good_enough = False

                if is_good_enough:
                    if operation == 'swap_translation':
                        current_option_indices[current_segmentation_idx] = max_idx
                    elif operation == 'swap_order':
                        current_order[current_segmentation_idx], current_order[max_idx] = current_order[max_idx], current_order[current_segmentation_idx]
                    elif operation == 'split_word':
                        new_option_indices[current_segmentation_idx:current_segmentation_idx+2] = option_idx_combinations[max_idx]
                        translation_options = new_translation_options
                        current_option_indices = new_option_indices
                        current_order = new_order
                        current_nailed_down_options = new_nailed_down_options
                        deepl_translations[current_segmentation_idx:current_segmentation_idx+1] = ['', '']
                        alignment_range = alignment_indices[current_segmentation_idx]
                        alignment_indices[current_segmentation_idx:current_segmentation_idx+1] = [
                            (alignment_range[0], alignment_range[0] + len(first_hz)),
                            (alignment_range[0] + len(first_hz), alignment_range[1]),
                        ]
                        hzs = new_hzs
                        prevent_split = new_prevent_split
                        print('SPLIT:', first_hz, second_hz, combined_translations[max_idx], max_similarity/best_similarity)

                    iterations_since_last_change = 0
                    pys = combined_pys[max_idx]
                    current_translation = combined_translations[max_idx]
                    best_similarity = max_similarity
                    if print_iterations:
                        print('BEST', current_translation, best_similarity)
                else:
                    iterations_since_last_change += 1
            else:
                iterations_since_last_change += 1

            current_segmentation_idx = (current_segmentation_idx + 1) % len(hzs)

    # If the best translation so far is empty, but there is a deepl translation, use that but with parens
    # Also, convert 's and 're to is and are
    for i, (curr_tr, deepl_tr) in enumerate(zip(current_translation, deepl_translations)):
        if curr_tr == '' and deepl_tr not in [None, '', '[UNK]']:
            current_translation[i] = deepl_tr
        elif curr_tr == "'s":
            current_translation[i] = 'is'
        elif curr_tr == "'re":
            current_translation[i] = 'are'
        # Convert back from e.g. "didn 't" to "didn't"
        current_translation[i] = current_translation[i].replace(" '", "'")

    pys = [py if py is not None else '' for py in pys]

    example_data = {
        'hzs': hzs,
        'pys': pys,
        'base_translations': base_translations,
        'deepl_translations': deepl_translations,
        'current_translation': [
            tr + ('*' if len(opts) > 1 else '') + ('+' if tr == d else '') + ('=' if n else '')
            for tr, opts, d, n in zip(current_translation, translation_options, deepl_translations, current_nailed_down_options)
        ],
    }

    print(json.dumps(example_data))

    return deepl_translations, current_translation, hzs, pys, alignment_indices, example_data

if __name__ == '__main__':
    for filename in ['good_examples.json', 'bad_examples.json']:
        with open(filename) as f:
            examples = json.load(f)

        for example in examples:
            print('')
            with Eval():
                last_idx = 0
                indices = []
                skip = []
                for hz in example['hzs']:
                    indices.append((last_idx, last_idx + len(hz)))
                    last_idx = last_idx + len(hz)
                    skip.append(False)

                _, translation, *_, data = get_embedding_word_translations(
                    example['hzs'],
                    example['pys'],
                    indices,
                    example['base_translations'],
                    skip,
                    example['deepl_translations'],
                    print_iterations=True
                )
                print(json.dumps(data))
