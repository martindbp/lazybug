import re
import json
import itertools
from functools import cache
from collections import defaultdict
from iteration_utilities import unique_everseen
from han import get_translation_options_cedict, CEDICT

import numpy as np
import torch
from torch.optim import Adam
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

def evaluate_configuration(config, translations, score_params):
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
    #  * for keeping low frequency chars together, e.g.  ?????? ??? better than ??? ??????
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
                if entry[-2] is not None:
                    max_freq = max(max_freq, entry[-2])

            information = -np.log(max(10e-8, max_freq))
            total_hz_information += max(0, information - torch.abs(score_params['hz_min_information'])) * torch.abs(score_params['hz_information_factor'])

        final_score += pow(total_hz_information, 2)

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
            information_factor = tr_information * torch.abs(score_params['information_factor'])
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


def get_segmentation_configurations(seg, translations, max_matches=3):
    word_translation_options = []
    for w in seg:
        # Find all cedict options with word morphologies and synonyms that match any of the translations
        cedict_opt = get_translation_options_matched_forms(w, *translations)

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

        #print(w, 'has', len(word_matches), 'matches')

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
        unique_matches = unique_matches[:max_matches]

        if len(unique_matches) == 0:
            unique_matches.append('noop')

        word_translation_options.append(unique_matches)

        #print('Reduced down to', len(unique_matches), 'matches')

    for combination in list(itertools.product(*word_translation_options)):
        yield (seg, combination)


def evaluate_configs(configurations, translations, score_params):
    configs_out = []
    config_scores_out = []
    max_config = None
    max_score = -float('inf')
    for config in configurations:
        score = evaluate_configuration(config, translations, score_params=score_params)
        configs_out.append(config)
        config_scores_out.append(score)
        if score > max_score:
            max_score = score
            max_config = config

    return config_scores_out, configs_out, max_score, max_config


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
    
    #print('Num segmentations', len(segmentations))
    #
    # Generate all possible configurations of segmentation PLUS matched translation options
    #

    configurations = None
    max_matches = 3
    while True:
        configurations = []
        for seg in segmentations:
            for config in get_segmentation_configurations(seg, translations, max_matches):
                configurations.append(config)

        if len(configurations) > 1000:
            max_matches = max(1, max_matches - 1)
            if max_matches == 1:
                break
            print('Too many configurations, lowering max_matches to', max_matches)
        else:
            break

    #print('Num configurations', len(configurations))
    e = evaluate_configs(configurations, translations, score_params)
    #print('done')
    return e


examples = [
    ("??????????????????????????????", "I just saw that you threw this", "Dad saw you put this.", "?????? ?????? ?????? ??? ??? ??????", "??? ??? ??? ?????? ??? ??? ??? ??? ???"),
    ("?????????????????????.", "Mute your phone.", "You turned that phone off.", "??? ??? ??? ?????? ??? ??? .", "??? ??? ??? ??? ?????? ??? ."),
    ("???????????????.", "The cycle passed.", "The cycle has been lifted.", "?????? ?????? ??? .", "?????? ??? ?????? ."),
    ("????????????????????????.", "Go from the east gate.", "You take the men in through the east gate.", "??? ??? ??? ??? ??? ??? ?????? .", "??? ??? ?????? ??? ??? ?????? ."),
    ("?????????????????????", "I just opened my eyes", "When I opened my eyes", "??? ?????? ?????? ??????", "??? ?????? ??? ?????? ???"),
    ("??????????????????.", "Someone from city bureau will come soon.", "The city will be here soon.", "??? ??? ?????? ??? ??? .", "?????? ?????? ??? ??? ."),
    ("??????????????????.", "We said there would be an accident.", "We said the car would crash.", "??? ??? ??? ??? ?????? .", "??? ??? ??? ??? ??? ??? ."),
    ("?????????", "that person", "that person", "?????????", "??? ??????"),
    ("??????????????????????????????.", "We will be questioned sooner or later.", "We'll be called in sooner or later.", "?????? ?????? ??? ??? ??? ?????? ??? .", "?????? ??? ?????? ??? ??? ?????? ??? ."),
    ("????????????????????????????", "Can I forget everything and attend the meeting then?", "And then you go to a meeting without a care in the world?", "?????? ???????????? ??? ?????? ?", "?????? ?????? ?????? ??? ?????? ?"),
    ("?????????????????????", "they would", "they would be present", "They'll both show up at", "?????? ??? ??? ?????? ???", "?????? ??? ??? ??? ??????"),
    ("???????????????", "have to check", "I have to find out", "??? ??? ?????? ???", "??? ??? ??? ??????"),
    #("???????????????????????????.", "The owner of the number is Xiao Heyun.", "The number belongs to a person named Xiao He-yun.", "?????? ?????? ??? ??? ????????? .", "?????? ?????? ??? ??? ??? ??? ??? ."),
    ("?????????????????????.", "It's the one who showed up on CCTV.", "That's the guy on the video.", "?????? ?????? ??? ??? ??? .", "??? ??? ?????? ??? ??? ??? ."),
    ("????????????????????????.", "I'm such a mess now.", "I'm very confused right now.", "??? ?????? ?????? ?????? ??? .", "??? ??? ??? ?????? ?????? ??? ."),
    ("??????????????????????????????.", "OK. You didn't mean it at first.", "You didn't mean the first one.", "??? ?????? ??? ?????? ?????? ??? ??? .", "??? ?????? ??? ??? ??? ?????? ??? ??? ."),
    ('???????????????.', "I'll just have to wear what I have.", 'Just wear it.', '?????? ??? ??? ??? .', '??? ?????? ??? ??? .'),
    ('??????????????????.', 'He explained it was because of his injury.', 'He said he had a foot problem.', '??? ??? ??? ??? ?????? .', '??? ??? ??? ??? ??? ??? .'),
    ('??????????????????,', 'After living in the northwest for years,', "I've been in the Northwest for many years,", '??? ??? ?????? ?????? ,', '??? ??? ?????? ??? ??? ,'),
    ('??????????????????????????????.', 'Well, it took me a good couple of days.', "It's been a few days.", '????????? ??? ??? ??? ?????? ??? ??? .', '?????? ??? ??? ??? ??? ?????? ??? ??? .'),
    ('???????????????????????????.', "I don't mind Chun'er.", 'There is nothing to be concerned about.', '??? ?????? ?????? ??? ?????? ??? .', '??? ?????? ??? ??? ??? ?????? ??? .'),
    ('??????????????????????????????.', "It's really unnecessary to stand out.", "You don't need to wear too much.", '?????? ??? ?????? ??? ??? ??? ??? ??? .', '??? ??? ??? ??? ??? ??? ??? ??? ??? ??? .'),
    ('?????????????????????????????????????', 'Why are you crying?', 'Why are you crying for no reason?', '?????? ????????? ??? ??? ??? ?????? ??? ??? ?', '?????? ??? ??? ??? ??? ??? ??? ?????? ??? ??? ?'),
    ('??????????????????????????????????????????.', 'It???s said to be made of ground white jasmine flowers.', 'It is said that the white jasmine flowers are ground and blended into it.', '??? ??? ??? ??? ????????? ?????? ??? ??? ?????? ??? .', '??? ??? ??? ??? ?????? ??? ?????? ??? ??? ?????? ??? .'),
    ('???????????????????????????.', 'A passbook, not too much money on it.', "And a bank book. There's no money.", '?????? ??? ?????? ????????? ??? .', '??? ??? ??? ?????? ????????? ??? .'),
    ('??????????????????.', "It's not far from here.", 'Not far from my place.', '??? ????????? ??? ??? .', '??? ??? ?????? ??? ??? .'),
    ('?????????????????????', 'saying his home was on fire', 'said that there was a fire at home', '??? ??? ?????? ?????? ???', '??? ??? ??? ??? ?????? ???'),
    ('???????????????????', 'What about the other passengers?', 'What about the other passengers?', '??? ?????? ?????? ??? ?', '??? ??? ??? ?????? ??? ?'),
    ('?????????????????????????????????.', 'You should be careful when you meet her.', 'You have to be careful when you see her in the future.', '??? ?????? ??? ??? ??? ??? ?????? ??? ??? .', '??? ??? ??? ??? ??? ??? ??? ?????? ??? ??? .'),
    ('?????????????????????.', 'The third one was this time.', 'The third time was this time.', '??? ?????? ?????? ?????? .', '??? ?????? ??? ??? ??? ??? .'),
    ('?????????????', 'What shall we do?', 'So what do we do?', '??? ????????? ?', '??? ?????? ??? ?'),
    ('???????????????.', 'Like, really old.', 'A very old one.', '?????? ??? ?????? .', '?????? ??? ??? ??? .'),
    ('???????????????????????????.', 'something like die together.', 'Something about wanting to die together.', '??? ??? ???????????? ????????? .', '??? ??? ???????????? ?????? ??? .'),
    ('?????????????????????.', 'Take it easy, little girl.', "Don't be nervous, young lady.", '?????? ?????? ??? ?????? .', '??? ??? ?????? ??? ?????? .'),
    ('????????????????', "Isn't it convenient?", 'How convenient is it to go back and forth?', '?????? ??? ?????? ?', '?????? ??? ??? ??? ?'),
    ('???????????????????????????.', 'He was always a model worker.', 'He was also always a model worker.', '??? ?????? ??? ??? ???????????? .', '??? ?????? ??? ??? ?????? ?????? .'),
    ("????????????????????????", "It's getting hot now.", "It's going to get hot.", "??? ?????? ??? ??? ??? ??? ???", "??? ????????? ??? ??? ??? ???"),

]

def create_value_tensor(val):
    return Variable(torch.tensor([val], dtype=float), requires_grad=True)


PYTORCH_SCORE_PARAMS = {
    'match_type_exact': create_value_tensor(1),
    'match_type_morphological': create_value_tensor(0.5),
    'match_type_synonym': create_value_tensor(0.3),
    'reuse_penalty': create_value_tensor(5),
    'information_factor': create_value_tensor(1/2),
    'option_information_ratio_factor': create_value_tensor(3),
    'hz_min_information': create_value_tensor(4),
    'hz_information_factor': create_value_tensor(0.8),
    #'hz_offset_information': create_value_tensor(0),
}


def forward():
    loss = 0
    scores = []
    num_incorrect = 0
    for hz, *translations, correct_seg, wrong_seg in examples:
        correct_configs = list(get_segmentation_configurations(correct_seg.split(' '), translations))
        wrong_configs = list(get_segmentation_configurations(wrong_seg.split(' '), translations))

        _, _, correct_score, _ = evaluate_configs(correct_configs, translations, PYTORCH_SCORE_PARAMS)
        _, _, wrong_score, _ = evaluate_configs(wrong_configs, translations, PYTORCH_SCORE_PARAMS)
        assert isinstance(correct_score, torch.Tensor) and isinstance(wrong_score,  torch.Tensor)
        scores.append((correct_score, wrong_score))
        if correct_score < wrong_score:
            num_incorrect += 1

    incorrect_factor = (len(examples) - num_incorrect) / num_incorrect
    print('incorrect_factor', incorrect_factor)

    for correct_score, wrong_score in scores:

        #loss += -torch.log(torch.sigmoid((correct_score - wrong_score)))
        item_loss = (wrong_score - correct_score) # + 0.1 * torch.sqrt(torch.pow(wrong_score, 2) + torch.pow(correct_score, 2))
        if item_loss > 0:
            item_loss_pow = torch.log(1 + item_loss) # incorrect_factor * item_loss
            print('adding loss for incorrect', item_loss.item(), '->', item_loss_pow.item())
            loss += item_loss_pow
        else:
            #add_loss = -torch.log(1 -item_loss)
            #print('for correct', item_loss.item(), '->', add_loss.item())
            #loss += add_loss
            pass

        #else:
            #print('not adding loss', item_loss)
#
        #loss += -torch.pow(wrong_score, 2) + torch.pow(correct_score, 2) - torch.abs(wrong_score) - torch.abs(correct_score)
        #if wrong_score > correct_score:
            #loss = -torch.pow(wrong_score - correct_score, 2)
        #else:
            #loss += torch.log(1 + correct_score - wrong_score)

        #loss += correct_score + wrong_score  # regularize so optimization doesn't just scale up scores

        #loss /= len(hz)  # normalize by length of string

    loss = loss / len(examples)
    w_regularization = sum(PYTORCH_SCORE_PARAMS.values(), 0)
    w_regularization = 0.1 * torch.sqrt(torch.pow(w_regularization, 2))
    loss += w_regularization
    loss.backward()
    print('Loss', loss)
    return loss, num_incorrect

ORIG = dict(PYTORCH_SCORE_PARAMS)
for key in ORIG:
    ORIG[key] = ORIG[key].clone()


def evaluate(score_params):
    num_correct = 0
    #for hz, *translations, correct_seg, wrong_seg in examples:
        #correct_configs = list(get_segmentation_configurations(correct_seg.split(' '), translations))
        #wrong_configs = list(get_segmentation_configurations(wrong_seg.split(' '), translations))

        #_, _, correct_score_before, _ = evaluate_configs(correct_configs, translations, ORIG)
        #_, _, wrong_score_before, _ = evaluate_configs(wrong_configs, translations, ORIG)

        #_, _, correct_score, _ = evaluate_configs(correct_configs, translations, score_params)
        #_, _, wrong_score, _ = evaluate_configs(wrong_configs, translations, score_params)
        #print(wrong_score_before, '->', wrong_score, '\t\t', correct_score_before, '->', correct_score)

    for hz, *translations, correct_seg, wrong_seg in examples:
        scores, configs, max_score, max_config = optimize_segmentation_pinyin_and_translations(
            hz, translations, score_params=score_params
        )
        max_config_str = ' '.join(max_config[0])
        if max_config_str == correct_seg:
            #print('CORRECT', max_score.item(), max_config_str)
            num_correct += 1
        else:
            print('INCORRECT', max_score.item(), max_config_str, 'should be', correct_seg)

        #max_wrong_score = -float('inf')
        #max_wrong_config = None
        #for score, config in zip(scores, configs):
            #if ' '.join(config[0]) != correct_seg and score > max_wrong_score:
                #max_wrong_score = score
                #max_wrong_config = config

        #print('Highest score wrong config:', max_wrong_score.item(), max_wrong_config)

    print('Accuracy:', num_correct / len(examples))


def train():
    adam = Adam(list(PYTORCH_SCORE_PARAMS.values()), lr=0.03)

    best_loss = float('inf')
    best_num_incorrect = float('inf')
    for t in range(50):
        loss, num_incorrect = forward()
        if num_incorrect < best_num_incorrect:
            best_num_incorrect = num_incorrect
            best_params = dict(PYTORCH_SCORE_PARAMS)
            print('Best params', best_params)
            for key in best_params:
                best_params[key] = best_params[key].clone()

        adam.step()

    evaluate(best_params)

if __name__ == '__main__':
    train()
    #evaluate(PYTORCH_SCORE_PARAMS)
