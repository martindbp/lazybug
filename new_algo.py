import re
import json
import itertools
from functools import cache
from collections import defaultdict
from iteration_utilities import unique_everseen
from han import get_translation_options_cedict, CEDICT

import numpy as np
import torch
from torch.autograd import Variable
from wordfreq import word_frequency
from word_forms.word_forms import get_word_forms

MANUAL_WORD_FORM_GROUPS = [
    {'you', 'your', "your's", "you"},
    {'I', 'me', "mine", "my", "I"},
    {'he', 'his', "he's", 'him'},
    {'she', 'her', "her's", "she"},
    {'we', 'our', "our's", "we"},
    {'will', 'would'},
    {'shall', 'should'},
]

def get_all_word_forms(word, pos=None):
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

SYNONYMS = defaultdict(list)
with open('data/git/en_thesaurus.jsonl', 'r') as f:
    lines = f.read().split('\n')
    for l in lines:
        if len(l.strip()) == 0:
            continue
        d = json.loads(l)
        SYNONYMS[d['word']] += d['synonyms']


def get_synonyms(word, check_other_forms=True):
    forms = get_all_word_forms(word) if check_other_forms else [word] 
    synonyms = []
    for form in forms:
        synonyms += SYNONYMS[form]

    return synonyms


EXACT_MATCH = 0
MORPHOLOGICAL_MATCH = 1
SYNONYM_MATCH = 2

DEFAULT_SCORE_PARAMS = {
    'match_type': {
        EXACT_MATCH: 1, MORPHOLOGICAL_MATCH: 0.5, SYNONYM_MATCH: 0.3
    },
    'reuse_penalty': 5,
    'information_factor': 1/2,
    'option_information_ratio_factor': 3,
    'hz_min_information': 4,
    'hz_max_information': 2,
    'hz_information_pow': 2,
}

def evaluate_configuration(config, translations, score_params=DEFAULT_SCORE_PARAMS):
    # Higher score for:
    #  * longer words (squared?)
    #  * longer translation matches
    #  * contiguous translation matches
    #  * non-overlapping matches
    #  * for longer names vs shorter names matched
    #  * for names that are capitalized
    #  * types of matching: exact > morphological > levenshtein > synonym
    #  * matching concentrated to a single full translation rather than spread out
    #  * low-frequency words
    #  * if pinyin matches cedict entry
    #  * for keeping low frequency chars together, e.g.  排查 出 better than 排 查出
    #

    def _get_score_param(key):
        val = score_params[key]
        if isinstance(val, torch.tensor):
            return val[0]
        return val

    segmentation = config[0]
    options = config[1]

    translation_scores = []
    min_frequency, max_frequency = float('inf'), 0
    for i in range(len(translations)):
        translation_scores.append([])
        for _ in range(len(translations[i])):
            translation_scores[-1].append(0.0)

        for word in re.findall(r'\b(\w+)\b', translations[i]):
            freq = word_frequency(word, 'en')
            min_frequency = min(freq, min_frequency)
            max_frequency = max(freq, max_frequency)

    final_score = 0
    seen_words_for_translation = set()
    for (hz, option) in zip(segmentation, options):
        # Prefer longer words, and grouping of high information characters
        total_hz_information = 0
        for char in hz:
            if char not in CEDICT.v:
                continue
            # If a char has multiple entries/pinyins, pick the most common for frequency/information
            max_freq = -float('inf')
            for entry in CEDICT.v[char][1]:
                max_freq = max(max_freq, entry[-2])

            if max_freq == 0:
                breakpoint()
            information = -np.log(max(10e-8, max_freq))
            total_hz_information += max(0, information - score_params['hz_min_information'])

        final_score += pow(total_hz_information / score_params['hz_max_information'], score_params['hz_information_pow'])

        if option == 'noop':  # no more score increase if there is no match for word
            continue

        option_translation = option[0]
        option_translation_length = sum([len(tr) for tr in option_translation])

        matches = option[2]
        option_information_ratio = score_params['option_information_ratio_factor'] * (pow(match_information_ratio(option), 2) - 0.5)

        for tr, translation_idx, start_idx, match_type in matches:
            if tr == 'noop':
                continue

            # Keep track of the maximum match score for each translation letter
            arr = translation_scores[translation_idx]
            tr_information = -np.log(max(10e-8, word_frequency(tr, 'en')))
            information_factor = tr_information * score_params['information_factor']
            name = 'exact'
            if match_type == MORPHOLOGICAL_MATCH:
                name = 'morphological'
            elif match_type == SYNONYM_MATCH:
                name = 'synonym'

            match_score = score_params['match_type_'+name] + information_factor + option_information_ratio
            for i in range(start_idx, start_idx+len(tr)):
                arr[i] = max(arr[i], match_score)

            if tr in seen_words_for_translation:
                final_score -= score_params['reuse_penalty']*match_score
            else:
                seen_words_for_translation.add(tr)

    for scores in translation_scores:
        last_score = 0
        for score in scores:
            if score == 0:
                final_score += last_score
                last_score = 0
            else:
                last_score = score

        final_score += last_score

    return final_score


def combinations(char_word_options, curr_options, curr_excluded_options, curr_idx):
    if curr_idx == len(char_word_options):
        return [curr_options]

    out = []
    if len(set(char_word_options[curr_idx]) & set(curr_options)) > 0:
        non_excluded = ['noop']
    else:
        non_excluded = [opt for opt in char_word_options[curr_idx] if opt not in curr_excluded_options]
        if len(non_excluded) == 0:
            non_excluded.append('noop')

    for option in non_excluded:
        if option in curr_options:
            continue

        excluded = list(char_word_options[curr_idx])
        if option != 'noop': excluded.remove(option)

        out += combinations(
            char_word_options,
            curr_options + ([option] if option != 'noop' else []),
            curr_excluded_options + excluded,
            curr_idx+1
        )

    return out


@cache
def get_translation_options_matched_forms(word, *translations):
    translation_options = get_translation_options_cedict(word, None, None, add_empty=False, split_or=False)

    translation_options_matched_forms = []
    for trs, _, py in translation_options:
        trs_matched_forms = []
        num_non_empty = 0
        for tr in trs:
            matched_forms = []
            for translation_idx, translation in enumerate(translations):
                # Get all exact, morphological and synonym forms
                exact = [tr]
                morphological = [f for f in get_all_word_forms(tr) if f not in exact and f.lower() not in exact]
                synonyms = [s for s in get_synonyms(tr) if s not in exact and s.lower() not in exact and s not in morphological and s.lower() not in morphological]
                forms = (
                    [(e, EXACT_MATCH) for e in exact] +
                    [(m, MORPHOLOGICAL_MATCH) for m in morphological] +
                    [(s, SYNONYM_MATCH) for s in synonyms]
                )

                for form, form_type in forms:
                    for it in re.finditer(f'(^|\s+|[^\w])({form})(\s+|$|[^\w])', translation, flags=re.IGNORECASE):
                        offset = len(it.groups()[0])
                        start_idx = it.span()[0] + offset
                        match_type = EXACT_MATCH if form == tr else MORPHOLOGICAL_MATCH
                        matched_forms.append((form, translation_idx, start_idx, form_type))

            matched_forms = sorted(matched_forms, key=lambda form: (form[1], form[2]))

            if len(matched_forms) > 0:
                num_non_empty += 1

            trs_matched_forms.append((tr, matched_forms))

        if num_non_empty > 0:
            translation_options_matched_forms.append((trs, py, trs_matched_forms))

    return translation_options_matched_forms


def match_information_ratio(match):
    # Calculates the ratio between the information of the matched words and all the words in the option
    total_information = 0
    total_matched_information = 0
    matched_words = []
    for w, (matched_w, *_) in zip(match[0], match[2]):
        word_information = -np.log(max(10e-8, word_frequency(w, 'en')))
        total_information += word_information
        if matched_w != 'noop':
            matched_word_information = min(-np.log(max(10e-8, word_frequency(matched_w, 'en'))), word_information)
            total_matched_information += matched_word_information
            matched_words.append(matched_w)

    ratio = total_matched_information / total_information
    return ratio


def optimize_segmentation_pinyin_and_translations(hz, translations, score_params):
    #
    # Get all possible words segmentations
    #
    words = []
    cedict = CEDICT.v
    char_word_options = []
    for _ in range(len(hz)):
        char_word_options.append([])

    for start_idx in range(len(hz)):
        for end_idx in range(start_idx+1, len(hz)+1):
            hz_word = hz[start_idx:end_idx]
            if hz_word in cedict or len(hz_word) == 1:
                words.append(hz_word)

                for idx in range(start_idx, end_idx):
                    char_word_options[idx].append(len(words)-1)

    segmentations = []
    for options in combinations(char_word_options, [], [], 0):
        option_words = [words[idx] for idx in options if idx != 'noop']
        segmentations.append(option_words)
        if ''.join([words[idx] for idx in options if idx != 'noop']) != hz:
            print(''.join([words[idx] for idx in options if idx != 'noop']))
            breakpoint()
    
    #
    # For each segmentation, find all cedict options with word morphologies and synonyms that match any of the translations
    #
    for segmentation in segmentations:
        for i, word in enumerate(segmentation):
            segmentation[i] = (word, get_translation_options_matched_forms(word, *translations))

    #print('Num segmentations', len(segmentations))
    #
    # Generate all possible configurations of segmentation PLUS matched translation options
    #
    configurations = []
    for seg in segmentations:
        word_translation_options = []
        for w, cedict_opt in seg:
            word_matches = []
            for tr, py, match_opts in cedict_opt:
                # Get all match combination, but only within each translation
                match_opts_for_translation = []
                for translation_idx in range(len(translations)):
                    filtered_match_opts = []
                    for tmp, matches in match_opts:
                        filtered_matches = [m for m in matches if m[1] == translation_idx]
                        if len(filtered_matches) == 0:
                            filtered_matches.append(('noop', None, None, None))  # needed for finding combinations, can't be empty
                        filtered_match_opts.append((tmp, filtered_matches))
                    match_opts_for_translation.append(filtered_match_opts)

                combs = [
                    list(itertools.islice(itertools.product(*[matches for _, matches in match_opts_for_translation[translation_idx]]), 10000))
                    for translation_idx in range(len(translations))
                ]
                combs = sum(combs, [])
                for combination in combs:
                    word_matches.append((tr, py, combination))

            # Only keep the shortest, highest score match for a translation word, e.g if we have:
            #   (['go'], [('go', 0, 3, 0)])
            # then we don't keep:
            #   (['to go'], [('noop', None, None, None), ('go', 0, 3, 0)])
            # since it can't possibly be better

            seen_matches = {}
            for tr, py, matches in word_matches:
                joined_match_str = ' '.join([str(match[:-1]) for match in matches if match[0] != 'noop'])  # NOTE: remove match_type before stringifying

                if joined_match_str == '':
                    continue
                _, _, prev = seen_matches.get(joined_match_str, (None, None, None))
                match_sum_types = sum([match[-1] for match in matches if match[0] != 'noop'])
                prev_sum_types = float('inf')
                if prev:
                    prev_sum_types = sum([match[-1] for match in prev if match[0] != 'noop'])

                if match_sum_types < prev_sum_types:
                    # Has better match types, overwrite
                    seen_matches[joined_match_str] = (tr, py, matches)

            unique_matches = list(seen_matches.values())

            # Calculate the overall information for each match (over the words in the option) and select the top N 
            unique_matches = sorted(unique_matches, key=match_information_ratio)
            unique_matches = unique_matches[:3]

            #num_noop_matches = []
            #word_matches = list(unique_everseen(word_matches, key=lambda x: json.dumps(x[1:])))
            #for tr, py, matches in word_matches:
                #num_non_noop = 0
                #for match in matches:
                    #if match[0] != 'noop':
                        #num_non_noop += 1

                #num_noop_matches.append((tr, py, matches, num_non_noop))

            #num_noop_matches = sorted(num_noop_matches, key=lambda x: -x[-1])
            #word_matches = [(tr, py, matches) for tr, py, matches, _ in num_noop_matches[:10]]

            if len(unique_matches) == 0:
                unique_matches.append('noop')

            word_translation_options.append(unique_matches)

        for combination in list(itertools.product(*word_translation_options)):
            words = [w for w, _ in seg]
            configurations.append((words, combination))

    #print('Num configurations', len(configurations))
    configs_out = []
    config_scores_out = []
    for config in configurations:
        score = evaluate_configuration(config, translations, score_params=score_params)
        configs_out.append(config)
        config_scores_out.append(score)

    return config_scores_out, configs_out


examples = [
    ("爸爸亲眼看见你把这个", "I just saw that you threw this", "Dad saw you put this.", "爸爸 亲眼 看见 你 把 这个", "爸 爸 亲 眼看 见 你 把 这 个"),
    ("你把那手机关了.", "Mute your phone.", "You turned that phone off.", "你 把 那 手机 关 了 .", "你 把 那 手 机关 了 ."),
    ("循环解除了.", "The cycle passed.", "The cycle has been lifted.", "循环 解除 了 .", "循环 解 除了 ."),
    ("你带人从东门进去.", "Go from the east gate.", "You take the men in through the east gate.", "你 带 人 从 东 门 进去 .", "你 带 人从 东 门 进去 ."),
    ("我刚一睁开眼睛", "I just opened my eyes", "When I opened my eyes", "我 刚一 睁开 眼睛", "我 刚一 睁 开眼 睛"),
    ("市里马上来人.", "Someone from city bureau will come soon.", "The city will be here soon.", "市 里 马上 来 人 .", "市里 马上 来 人 ."),
    ("说了车会出事.", "We said there would be an accident.", "We said the car would crash.", "说 了 车 会 出事 .", "说 了 车 会 出 事 ."),
    ("那个人", "that person", "that person", "那个人", "那 个人"),
    ("我们早晚会被叫过去的.", "We will be questioned sooner or later.", "We'll be called in sooner or later.", "我们 早晚 会 被 叫 过去 的 .", "我们 早 晚会 被 叫 过去 的 ."),
    ("然后不管不顾去开会?", "Can I forget everything and attend the meeting then?", "And then you go to a meeting without a care in the world?", "然后 不管不顾 去 开会 ?", "然后 不管 不顾 去 开会 ?"),
    ("他们俩会出现在", "they would", "they would be present", "They'll both show up at", "他们 俩 会 出现 在", "他们 俩 会 出 现在"),
    ("得先排查出", "have to check", "I have to find out", "得 先 排查 出", "得 先 排 查出"),
    ("号码归属人叫肖鹤云." "The owner of the number is Xiao Heyun.", "The number belongs to a person named Xiao He-yun.", "号码 归属 人 叫 肖鹤云 .", "号码 归属 人叫 肖 鹤云 ."),
]

def create_value_tensor(val):
    return Variable(torch.tensor([val], dtype=float), requires_grad=True)

#match_type_exact 0.9694201295132068 -7.626661859708163
#match_type_morphological 0.5213996370906425 5.822887178702049
#match_type_synonym 0.32009879693532994 6.417889504537964
#reuse_penalty 5.15764999800173 39.50457953686117
#information_factor 0.6386526121647206 44.13881984612936
#option_information_ratio_factor 2.9866223496092466 -3.1817329031770787
#hz_min_information 4.377319436260156 65.10725346690772
#hz_max_information 2.7942716962033383 128.11959193275166
#hz_information_pow 1.1098594089505958 -144.46985999531228

#PYTORCH_SCORE_PARAMS = {
    #'match_type_exact': create_value_tensor(0.97),
    #'match_type_morphological': create_value_tensor(0.52),
    #'match_type_synonym': create_value_tensor(0.32),
    #'reuse_penalty': create_value_tensor(5.15),
    #'information_factor': create_value_tensor(0.64),
    #'option_information_ratio_factor': create_value_tensor(2.98),
    #'hz_min_information': create_value_tensor(4.37),
    #'hz_max_information': create_value_tensor(2.79),
    #'hz_information_pow': create_value_tensor(1.1),
#}


PYTORCH_SCORE_PARAMS = {
    'match_type_exact': create_value_tensor(1),
    'match_type_morphological': create_value_tensor(0.5),
    'match_type_synonym': create_value_tensor(0.3),
    'reuse_penalty': create_value_tensor(5),
    'information_factor': create_value_tensor(1/2),
    'option_information_ratio_factor': create_value_tensor(3),
    'hz_min_information': create_value_tensor(4),
    'hz_max_information': create_value_tensor(2),
    'hz_information_pow': create_value_tensor(2),
}


def forward():
    loss = 0
    for hz, *translations, correct_seg, wrong_seg in examples:
        scores, configs = optimize_segmentation_pinyin_and_translations(
            hz, translations, score_params=PYTORCH_SCORE_PARAMS
        )
        config_scores = {}
        for score, config in zip(scores, configs):
            config_scores[' '.join(config[0])] = score

        correct_score = config_scores.get(correct_seg, 0)
        wrong_score = config_scores.get(wrong_seg, 0)
        if wrong_score > correct_score:
            loss += correct_score - wrong_score
        else:
            loss += torch.log(1 + correct_score - wrong_score)
        #loss += min(10, correct_score - score)

    loss = loss / len(examples)
    loss.backward()
    print('Loss', loss)

learning_rate = 1e-2
for t in range(100):
    forward()

    for key, val in PYTORCH_SCORE_PARAMS.items():
        if val.grad:
            print(key, val.data.item(), val.grad.data.item())
            val.data += learning_rate * val.grad.data.item()
        else:
            print(key, None)
    #learning_rate *= 1/2

#print('Sum score:', sum_score)
