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
                if entry[-2] is not None:
                    max_freq = max(max_freq, entry[-2])

            information = 10 if max_freq == -float('inf') else -np.log(max(10e-8, max_freq))
            total_hz_information += max(0, information - torch.abs(score_params['hz_min_information']))

        final_score += pow(max(0, (total_hz_information - torch.abs(score_params['hz_offset_information']))), 2) * torch.abs(score_params['hz_max_information'])

        if option == 'noop':  # no more score increase if there is no match for word
            continue

        option_translation = option[0]
        option_translation_length = sum([len(tr) for tr in option_translation])

        matches = option[2]
        option_information_ratio = torch.abs(score_params['option_information_ratio_factor']) * (pow(match_information_ratio(option), 2) - 0.5)

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
    
    print('Num segmentations', len(segmentations))
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

    print('Num configurations', len(configurations))
    e = evaluate_configs(configurations, translations, score_params)
    print('done')
    return e


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
    #("号码归属人叫肖鹤云.", "The owner of the number is Xiao Heyun.", "The number belongs to a person named Xiao He-yun.", "号码 归属 人 叫 肖鹤云 .", "号码 归属 人 叫 肖 鹤 云 ."),
    ("就是视频上那人.", "It's the one who showed up on CCTV.", "That's the guy on the video.", "就是 视频 上 那 人 .", "就 是 视频 上 那 人 ."),
    ("我现在脑子特别乱.", "I'm such a mess now.", "I'm very confused right now.", "我 现在 脑子 特别 乱 .", "我 现 在 脑子 特别 乱 ."),
    ("你第一个不是故意的行.", "OK. You didn't mean it at first.", "You didn't mean the first one.", "你 第一 个 不是 故意 的 行 .", "你 第一 个 不 是 故意 的 行 ."),
    ('将就着戴吧.', "I'll just have to wear what I have.", 'Just wear it.', '将就 着 戴 吧 .', '将 就着 戴 吧 .'),
    ('说是足疾发作.', 'He explained it was because of his injury.', 'He said he had a foot problem.', '说 是 足 疾 发作 .', '说 是 足 疾 发 作 .'),
    ('臣在西北多年,', 'After living in the northwest for years,', "I've been in the Northwest for many years,", '臣 在 西北 多年 ,', '臣 在 西北 多 年 ,'),
    ('可不是嘛绣了好几日呢.', 'Well, it took me a good couple of days.', "It's been a few days.", '可不是 嘛 绣 了 好几 日 呢 .', '可不 是 嘛 绣 了 好几 日 呢 .'),
    ('有什么计较不计较的.', "I don't mind Chun'er.", 'There is nothing to be concerned about.', '有 什么 计较 不 计较 的 .', '有 什么 计 较 不 计较 的 .'),
    ('实在不需要穿得太出挑.', "It's really unnecessary to stand out.", "You don't need to wear too much.", '实在 不 需要 穿 得 太 出 挑 .', '实 在 不 需 要 穿 得 太 出 挑 .'),
    ('怎么好端端地就哭起来了呢?', 'Why are you crying?', 'Why are you crying for no reason?', '怎么 好端端 地 就 哭 起来 了 呢 ?', '怎么 好 端 端 地 就 哭 起来 了 呢 ?'),
    ('说是用白茉莉花磨碎了兑进去的.', 'It’s said to be made of ground white jasmine flowers.', 'It is said that the white jasmine flowers are ground and blended into it.', '说 是 用 白 茉莉花 磨碎 了 兑 进去 的 .', '说 是 用 白 茉莉 花 磨碎 了 兑 进去 的 .'),
    ('还有个存折没什么钱.', 'A passbook, not too much money on it.', "And a bank book. There's no money.", '还有 个 存折 没什么 钱 .', '还 有 个 存折 没什么 钱 .'),
    ('离我这儿不远.', "It's not far from here.", 'Not far from my place.', '离 我这儿 不 远 .', '离 我 这儿 不 远 .'),
    ('说是家里着火了', 'saying his home was on fire', 'said that there was a fire at home', '说 是 家里 着火 了', '说 是 家 里 着火 了'),
    ('那其他乘客呢?', 'What about the other passengers?', 'What about the other passengers?', '那 其他 乘客 呢 ?', '那 其 他 乘客 呢 ?'),
    ('你以后见她可得注意着点.', 'You should be careful when you meet her.', 'You have to be careful when you see her in the future.', '你 以后 见 她 可 得 注意 着 点 .', '你 以 后 见 她 可 得 注意 着 点 .'),
    ('第三次就是这次.', 'The third one was this time.', 'The third time was this time.', '第 三次 就是 这次 .', '第 三次 就 是 这 次 .'),
    ('那怎么办?', 'What shall we do?', 'So what do we do?', '那 怎么办 ?', '那 怎么 办 ?'),
    ('特别老那种.', 'Like, really old.', 'A very old one.', '特别 老 那种 .', '特别 老 那 种 .'),
    ('说要同归于尽什么的.', 'something like die together.', 'Something about wanting to die together.', '说 要 同归于尽 什么的 .', '说 要 同归于尽 什么 的 .'),
    ('不用紧张小姑娘.', 'Take it easy, little girl.', "Don't be nervous, young lady.", '不用 紧张 小 姑娘 .', '不 用 紧张 小 姑娘 .'),
    ('来回多方便?', "Isn't it convenient?", 'How convenient is it to go back and forth?', '来回 多 方便 ?', '来回 多 方 便 ?'),
    ('还一直都是劳动模范.', 'He was always a model worker.', 'He was also always a model worker.', '还 一直 都 是 劳动模范 .', '还 一直 都 是 劳动 模范 .'),
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
    'hz_max_information': create_value_tensor(1/2),
    'hz_offset_information': create_value_tensor(0),
}


def forward():
    loss = 0
    for hz, *translations, correct_seg, wrong_seg in examples:
        correct_configs = list(get_segmentation_configurations(correct_seg.split(' '), translations))
        wrong_configs = list(get_segmentation_configurations(wrong_seg.split(' '), translations))

        _, _, correct_score, _ = evaluate_configs(correct_configs, translations, PYTORCH_SCORE_PARAMS)
        _, _, wrong_score, _ = evaluate_configs(wrong_configs, translations, PYTORCH_SCORE_PARAMS)
        assert isinstance(correct_score, torch.Tensor) and isinstance(wrong_score,  torch.Tensor)

        #loss += -torch.log(torch.sigmoid((correct_score - wrong_score)))
        item_loss = (wrong_score - correct_score) # + 0.1 * torch.sqrt(torch.pow(wrong_score, 2) + torch.pow(correct_score, 2))
        if item_loss > 0:
            item_loss = torch.pow(item_loss, 2)
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
    return loss

ORIG = dict(PYTORCH_SCORE_PARAMS)
for key in ORIG:
    ORIG[key] = ORIG[key].clone()


def evaluate(score_params):
    for hz, *translations, correct_seg, wrong_seg in examples:
        correct_configs = list(get_segmentation_configurations(correct_seg.split(' '), translations))
        wrong_configs = list(get_segmentation_configurations(wrong_seg.split(' '), translations))

        _, _, correct_score_before, _ = evaluate_configs(correct_configs, translations, ORIG)
        _, _, wrong_score_before, _ = evaluate_configs(wrong_configs, translations, ORIG)

        _, _, correct_score, _ = evaluate_configs(correct_configs, translations, score_params)
        _, _, wrong_score, _ = evaluate_configs(wrong_configs, translations, score_params)
        print(wrong_score_before, '->', wrong_score, '\t\t', correct_score_before, '->', correct_score)

    for hz, *translations, correct_seg, wrong_seg in examples:
        scores, configs, max_score, max_config = optimize_segmentation_pinyin_and_translations(
            hz, translations, score_params=score_params
        )
        max_config_str = ' '.join(max_config[0])
        if max_config_str == correct_seg:
            print('CORRECT', max_score.item(), max_config_str)
        else:
            print('INCORRECT', max_score.item(), max_config_str, 'should be', correct_seg)

        max_wrong_score = -float('inf')
        max_wrong_config = None
        for score, config in zip(scores, configs):
            if ' '.join(config[0]) != correct_seg and score > max_wrong_score:
                max_wrong_score = score
                max_wrong_config = config

        print('Highest score wrong config:', max_wrong_score.item(), max_wrong_config)


def train():
    adam = Adam(list(PYTORCH_SCORE_PARAMS.values()), lr=0.03)

    best_loss = float('inf')
    for t in range(50):
        loss = forward()
        if loss < best_loss:
            best_loss = loss
            best_params = dict(PYTORCH_SCORE_PARAMS)
            print('Best params', best_params)
            for key in best_params:
                best_params[key] = best_params[key].clone()

        adam.step()

    evaluate(best_params)

if __name__ == '__main__':
    train()
    #evaluate(PYTORCH_SCORE_PARAMS)
