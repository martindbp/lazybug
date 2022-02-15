import re
import os
import sys
import subprocess

import jieba_fast as jieba
import jieba_fast.posseg as pseg

from merkl import task, batch, FileRef, Eval

from wrapped_json import json
from pinyin import normalized_to_diacritical, extract_normalized_pinyin
from han import filter_text_hanzi, CEDICT

from process_translations import ENGLISH_MWS, match_fixed_translation, get_translations, get_single_translations_batch
from sentence_embedding_translations import get_embedding_word_translations


@task(serializer=json)
def add_segmentation_and_alignment(caption_data, alignment_translations, show_names_list):
    hanzis = [' '.join(line[0]) for line in caption_data['lines']]
    translations = [line[7] for line in caption_data['lines']]
    alignment_line_translations = [transl for (transl, *_) in alignment_translations]
    translation_words = [words for (_, words, _) in alignment_translations]
    indices = [indices for (_, _, indices) in alignment_translations]
    show_names_dict = {name: transl for name, transl in show_names_list}

    datas = []
    empty_translations = []
    all_embedding_translations, all_embedding_hzs, all_embedding_pys, all_embedding_indices = [], [], [], []
    for line_idx, (sentence_hz, sentence_translations, words, word_indices, alignment_line_transl) in enumerate(zip(
        hanzis, translations, translation_words, indices, alignment_line_translations
    )):
        include_idx = 0
        print(sentence_hz)

        deepl_transls = []
        hzs = []
        pys = []
        indices = []
        skip = []
        for i, ((from_idx, to_idx, word_hz), pos, py, include, seg_type) in enumerate(word_indices):
            word_hz = word_hz.strip()
            transl = ''
            if seg_type == 'mw':  # measure word
                transl = '[MW]'
                if word_hz not in ENGLISH_MWS:
                    seg_type = 'skip'
            elif seg_type == 'person':
                if word_hz in show_names_dict:
                    transl = show_names_dict[word_hz]
                else:
                    transl = re.sub('[1-5]', '', py).capitalize()
                py = py.capitalize()
            elif seg_type == 'skip':
                transl = ''
            elif include:
                transl = words[include_idx]

            if (transl != '[MW]' and transl != '') and include:
                include_idx += 1

            deepl_transls.append(transl)
            hzs.append(word_hz)
            pys.append(py)
            indices.append((from_idx, to_idx))
            skip.append(seg_type == 'skip')

        with Eval():
            (
                deepl_transls,
                embedding_translations,
                embedding_hzs,
                embedding_pys,
                embedding_indices,
                data
            ) = get_embedding_word_translations(
                hzs,
                pys,
                indices,
                sentence_translations + [alignment_line_transl],
                skip,
                deepl_transls,
                print_iterations=True,
            )

        all_embedding_translations.append(embedding_translations)
        all_embedding_hzs.append(embedding_hzs)
        all_embedding_pys.append(embedding_pys)
        all_embedding_indices.append(embedding_indices)
        datas.append(data)

        # Update the translations with the fixed translations where empty
        for i, (deepl_transl, transl, hz, py) in enumerate(zip(deepl_transls, embedding_translations, embedding_hzs, embedding_pys)):
            if transl is None:
                continue

            hz = hz.strip()
            fixed_translation = match_fixed_translation(hz, py)
            if fixed_translation is not None and transl != '[MW]':
                transl = fixed_translation

            embedding_translations[i] = transl
            if transl == '' and py != '':
                print('EMPTY', hz, py)
                empty_translations.append(hz)

    deepl_dict = {}
    if len(empty_translations) > 0:
        with open('data/remote/private/deepl_dict.json', 'r') as f:
            deepl_dict = json.load(f)

        deepl_empty_translations = []
        for empty_hz in empty_translations:
            if empty_hz not in deepl_dict:
                deepl_dict[empty_hz] = get_translations([empty_hz]).eval()[0].lower()

        with open('data/remote/private/deepl_dict.json', 'w') as f:
            json.dump(deepl_dict, f)

    all_line_alignments = []
    for line_idx, (embedding_translations, embedding_hzs, embedding_pys, embedding_indices) in enumerate(zip(all_embedding_translations, all_embedding_hzs, all_embedding_pys, all_embedding_indices)):
        line_alignments = []
        for transl, hz, py, idx_range in zip(embedding_translations, embedding_hzs, embedding_pys, embedding_indices):
            hz = hz.strip()
            if transl is None:
                continue

            if transl == '' and py != '':
                transl = deepl_dict.get(hz, '')

            # The front end needs the py parts separate, with both diacriticals and numbers
            py_parts = [(normalized_to_diacritical(py_part), py_part) for py_part in extract_normalized_pinyin(py)]

            alignment = (
                idx_range[0],
                idx_range[1],
                hz.strip(),
                py_parts,
                transl,
            )
            line_alignments.append(alignment)

        all_line_alignments.append(line_alignments)


    with open(f'out_examples_{caption_data["caption_id"]}.json', 'w') as f:
        json.dump(datas, f)

    for line, line_alignment, alignment_line_transl in zip(caption_data['lines'], all_line_alignments, alignment_line_translations):
        line[-1].append(alignment_line_transl)
        line.append(line_alignment)

    return caption_data
