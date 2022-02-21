import re
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

import pyperclip
from wrapped_json import json
from merkl import task, Eval, batch
import transformer_segmentation
from transformer_segmentation import segment_sentences, segmentations_to_pinyin, join_names_present_in_translations
from han import filter_text_hanzi, get_idioms, is_mw_according_to_cedict, is_name_according_to_cedict, CEDICT, clean_cedict_translation
from sentence_embedding_translations import get_options, get_translation_options_cedict
from english import STOPWORDS


ENGLISH_MWS = [
    '盒', '双', '杯', '平', '堆', '包', '卷', '桶', '束', '次', '阵', '刻', '番', '栋', '份', '片', '块', '口',
    '碗', '盘', '滴', '壶', '罐', '些', '种', '群', '众', '帮', '班', '排', '队', '串', '打', '叠', '秒', '分', '天',
    '日', '周', '年', '代', '斤', '吨', '磅', '坪', '块', '毛', '笔', '寸', '尺', '里', '升', '斗', '度', '声', '岁',
    '平方公里', '瓶', '伙',
    '出', # (classifier for plays or chapters of classical novels)/
]

SKIP_TRANSLATIONS = [
    ('我', 'I'),
    ('我的', 'my'),
    ('我们', 'we'),
    ('我们的', 'our'),
    ('你', 'you'),
    ('您', 'you'),
    ('你们', 'you'),
    ('你的', 'your'),
    ('你们的', 'your'),
    ('他', 'he'),
    ('他的', 'his'),
    ('他们', 'they'),
    ('他们的', 'their'),
    ('她', 'she'),
    ('她的', 'her'),
    ('她们', 'they'),
    ('她们的', 'their'),
    ('它', 'it'),
    ('它的', 'its'),
    ('它们', 'they'),
    ('它们的', 'their'),
    ('跟', 'with'),
    ('个', 'a'),
    ('说', 'say'),
    ('这', 'this'),
    ('那', 'that/then'),
    ('找', 'find'),
    ('先', 'first'),
    ('也', 'also'),
    ('卖', 'sell'),
    ('买', 'buy'),
    ('得', 'dei3', 'must'),
]

FIXED_TRANSLATIONS = [
    ('的话', 'de5hua4', 'if'),
    ('的', '[de]'),
    ('啊', '[a]'), 
    ('吗', '[ma]'),
    ('呗', '[bei]'),
    ('嘛', '[ma]'), 
    ('呀', '[ya]'),
    ('喽', '[lou]'),
    ('哟', '[yo]'),
    ('过', 'guo5', '[guo]'),
    ('了', 'le5', '[le]'),
    ('地', 'de5', '[de]'),
    ('啦', '[la]'),
    ('吧', '[ba]'),
    ('呢', '[ne]'),
    ('着', '[zhe]'),
    ('把', 'take'),
    ('得', 'de5', '[de]'),
    ('得', 'de2', '[de]'),
    ('哪', 'na5', '[na]'),
]


idioms = None
def match_fixed_translation(hz, py):
    global idioms
    if idioms is None:
        idioms = get_idioms().eval()
    for item in FIXED_TRANSLATIONS:
        if len(item) == 2:
            item_hz, item_tr = item
            item_py = None
        else:
            item_hz, item_py, item_tr = item

        if hz == item_hz and (py == item_py or item_py == None):
            return item_tr

    if hz in idioms:
        return idioms[hz]

    return None


def _get_translations(all_lines, automated=True):
    if automated:
        # Create a temporary server that receives the polling for input from
        # the DeepL automation browser extension, sends the text to be
        # translated, then waits for the POST reply with the translation
        text = '\n'.join(all_lines)
        print('Waiting to get translation from extension: ')
        print(text)
        print('Open URL: https://www.deepl.com/translator#zh/en/')
        translation = None

        class DeeplRequestHandler(BaseHTTPRequestHandler):

            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(bytes(text, 'utf-8'))
                print('Sent text to extension')

            def do_POST(self):
                nonlocal translation
                content_length = int(self.headers['Content-Length'])
                translation = str(self.rfile.read(content_length), 'utf-8')
                self.send_response(200)
                self.end_headers()
                raise KeyboardInterrupt

        httpd = HTTPServer(('localhost', 8000), DeeplRequestHandler)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('Shutdown, have translation: ', translation)
            input_translation_lines = translation.split('\n')

    else:  # manual copy/paste
        print('\n'.join(all_lines))
        print('\nLines have been copied to clipboard')
        pyperclip.copy('\n'.join(all_lines))
        print("\nPaste the translation here:\n")
        input_translation_lines = []
        try:
            while True:
                input_translation_lines.append(input())
        except KeyboardInterrupt:
            pass
        print('')

    if len(input_translation_lines) != len(all_lines):
        raise Exception

    return input_translation_lines


@task(serializer=json, hash_key='deepl_translation')
def get_translations(all_lines):
    return _get_translations(all_lines)


@batch(get_translations, hash_key='deepl_translation')
def get_single_translations_batch(all_lines):
    return _get_translations(all_lines)


@task(serializer=json)
def get_machine_translations(caption_data):
    """ This function requires the user to manually copy/paste the hanzi captions into DeepL translation services
    and copy/paste back the translations. Why? Cheaper than using the API """
    all_lines = [' '.join(line[0]) for line in caption_data['lines']]
    translation_lines = get_translations(all_lines)
    translation_lines >> f'data/remote/private/translation_cache/{caption_data["caption_id"]}_{translation_lines.hash}.json'
    translation_lines = translation_lines.eval()
    return translation_lines


@task(serializer=json, deps=[transformer_segmentation, get_idioms])
def get_alignment_translations(caption_data, global_known_names=[], fixed_translations={}):
    lines = caption_data['lines']

    all_lines = [' '.join(line[0]) for line in lines]
    all_translations = [line[7] for line in lines]

    print('num lines:', len(all_lines))
    with Eval():
        all_segments = segment_sentences(all_lines, join_compound_words=True)
        all_pys = segmentations_to_pinyin(all_segments)
        all_segments, all_pys, confirmed_names = join_names_present_in_translations(all_segments, all_pys, all_translations, global_known_names, fixed_translations)

    print('num segments:', len(all_segments))
    print('num pys:', len(all_pys))

    ner_people = []
    for (_, _, _, people, _) in all_segments:
        ner_people += people

    confirmed_people = global_known_names + confirmed_names # + ner_people
    confirmed_people_hz = set(p[0] for p in confirmed_people)

    out_lines = []
    out_indices_json = []
    include_indices = []
    num_non_empty_out = 0
    for sentence_hz, (segs, psos, ners, ner_people, *_), pys, transls in zip(all_lines, all_segments, all_pys, all_translations):
        filtered_segments = []
        ner_people_hz = set(p[0] for p in ner_people)

        hzs = [seg[-1].strip() for seg in segs]
        #_, translation_options, options_nailed_down, _ = get_options(hzs, transls, pys)
        #for hz, seg, pos, py, nailed_down in zip(hzs, segs, psos, pys, options_nailed_down):

        for hz, seg, pos, py in zip(hzs, segs, psos, pys):
            seg_type = None
            include = False
            
            #if nailed_down:
                #seg_type = 'nailed_down'
            if len(filter_text_hanzi(hz)) == 0:
                seg_type = 'empty'
            elif pos == 'Nf' and hz not in ENGLISH_MWS and is_mw_according_to_cedict(hz, py):
                seg_type = 'mw'  # measure word
            elif match_fixed_translation(hz, py) is not None:
                seg_type = 'skip'
            elif hz in confirmed_people_hz or hz in ner_people:
                seg_type = 'name'
            elif hz in fixed_translations:
                if fixed_translations[hz][0].isupper():
                    seg_type = 'name'
                else:
                    seg_type = 'fixed_translation'
            else:
                include = True

            filtered_segments.append((seg, pos, py, include, seg_type))

        # Put some words last, because they tend to mess up translations that come after
        indexed_filtered_segments = list(enumerate(filtered_segments))
        put_last = [seg[-1] == '才' for (seg, *_) in filtered_segments]
        indexed_filtered_segments = sorted(list(zip(indexed_filtered_segments, put_last)), key=lambda x: x[1])
        indexed_filtered_segments = [idx_seg for (idx_seg, last) in indexed_filtered_segments]

        out = ''
        sentence_include_indices = []
        for i, (seg, pos, py, include, _) in indexed_filtered_segments:
            if include:
                out += f'{i+1}. {seg[-1].strip()} '
                sentence_include_indices.append(i)

        sentence_include_indices = list(sorted(sentence_include_indices))

        out_indices_json.append(filtered_segments)
        out_lines.append(f'"{sentence_hz}"')
        out_lines.append(out)
        include_indices.append(sentence_include_indices)

    out_line_is_empty = [out == '' for out in out_lines]
    translation_lines = get_translations([out for out in out_lines if out != ''])
    translation_lines >> f'data/remote/private/translation_cache/{caption_data["caption_id"]}_{translation_lines.hash}_alignments.json'
    translation_lines = translation_lines.eval()

    translation_lines_final = []
    next_translation_idx = 0
    for is_empty in out_line_is_empty:
        if is_empty:
            translation_lines_final.append('')
        else:
            translation_lines_final.append(translation_lines[next_translation_idx])
            next_translation_idx += 1

    alignment_translations = translation_lines_final[::2]
    final_translations = []
    for transl in alignment_translations:
        try:
            final_translations.append(re.findall('\"(.*)\"', transl)[0])
        except:
            # One of the " is probably missing
            transl = transl.strip().strip('"')
            final_translations.append(transl)

    word_translations = translation_lines_final[1::2]
    translation_words = []
    for indices, words_str, segs, pys, transls in zip(include_indices, word_translations, out_indices_json, all_pys, all_translations):
        words_str = words_str.strip()
        matched_words = [(int(idx)-1, w.strip()) for idx, w in re.findall('([0-9]+)\.(.*?)(?=[0-9]+\.|$)', words_str)]
        words = [''] * len(segs)
        for idx, w in matched_words:
            # Sometimes the translation that comes back has a trailing dot. We should always remove it unless it's
            # part of an acronym like "the U.S.". So check for if there are more dots before it
            if '.' not in w[-5:-1]:
                w = w.strip('.')
            w = w.strip(',')  # always strip commas

            lstrip = ['to ', 'the ', 'be ']
            for s in lstrip:
                if w.startswith(s):
                    w = w[len(s):]

            try:
                words[idx] = w
            except:
                break

        words = [words[idx] for idx in indices]
        #pys = [pys[idx] for idx in indices]

        # If we get consecutive equal translations, or one containing the other, it's probably a translation error
        last_transl = '[UNK]'
        last_hz = None
        segs = [segs[idx] for idx in indices]
        for i, (transl, seg) in enumerate(zip(words, segs)):
            hz = seg[0][-1]
            # Remove spaces so they don't affect ratio
            transl_len = len(transl.replace(' ', ''))
            last_transl_len = len(last_transl.replace(' ', ''))
            ratio = min(transl_len, last_transl_len) / max(transl_len, last_transl_len)
            if hz != last_hz and (transl == last_transl or transl in last_transl.split(' ') or last_transl in transl.split(' ')) and ratio > 0.4:
                print('Zeroing out ', transl, last_transl, hz, last_hz, words)
                if i > 0:
                    words[i-1] = '[UNK]'
                words[i] = '[UNK]'

            last_transl = transl if transl != '' else '[UNK]'
            last_hz = hz

        # * Zero out neighboring translations if a translation is empty
        # * Remove Deepl translations that are too long compared to length of hanzi are likely errors
        # * Remove Deepl translations that are a superset of a cedict translation
        # * Remove deepl translations that are just stopwords
        # * Remove translations with hanzi in them
        for i, (transl, seg) in enumerate(zip(words, segs)):
            seg, *_ = seg
            hz = seg[-1]
            if transl == '' and hz in CEDICT.v:
                print('Zeroing out')
                print(words[i-1:i+2])
                print(segs[i-1:i+2])
                if i > 0:
                    words[i-1] = '[UNK]'
                words[i] = '[UNK]'
                if i < len(words) - 1:
                    words[i+1] = '[UNK]'

            is_in_baseline = True in [transl in baseline for baseline in transls]
            has_no_dict_entry = hz not in CEDICT.v
            num_transl_words = len(transl.split(' '))
            if (has_no_dict_entry or is_in_baseline) and num_transl_words / len(hz) >= 2:
                print(f'Zeroing out {hz} "{transl}" because too long, and exists in baseline {transls}')
                words[i] = '[UNK]'

            if not has_no_dict_entry:
                options = get_translation_options_cedict(hz, py=None, deepl=None, add_empty=False, split_or=False)
                cleaned_transl = clean_cedict_translation(transl, py=None, split_or=False)
                if len(cleaned_transl) == 0:
                    print('Zeroing out', hz, min_option, cleaned_transl)
                    words[i] = '[UNK]'
                else:
                    cleaned_transl = [c.lower() for c in cleaned_transl[0].split(' ') if c.lower()]
                    if len(cleaned_transl) > 0:
                        min_option = None
                        for option in options:
                            option = [o.lower() for o in option[0]]
                            intersection = set(cleaned_transl) & set(option)
                            if len(intersection) == min(len(option), len(cleaned_transl)):
                                if min_option is None:
                                    min_option = option
                                else:
                                    diff_option = abs(len(option) - len(cleaned_transl))
                                    diff_min_option = abs(len(min_option) - len(cleaned_transl))
                                    if min_option is None or diff_option < diff_min_option:
                                        min_option = option

                        if min_option is not None and len(min_option) != len(cleaned_transl) and min(len(min_option), len(cleaned_transl)) != 0:
                            print('Zeroing out deepl contained in cedict option', hz, min_option, cleaned_transl)
                            words[i] = '[UNK]'

            if transl.replace("'", "").lower() in STOPWORDS:
                words[i] = '[UNK]'

            if len(filter_text_hanzi(words[i])) > 0:
                words[i] = '[UNK]'

        translation_words.append(words)

    return list(zip(final_translations, translation_words, out_indices_json))
