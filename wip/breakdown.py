"""
Create breakdown lists of compound characters that are easily understood if their components are understood
"""
from merkl import task
from han import CEDICT, filter_text_hanzi

@task
def get_cedict_breakdown_characters():
    breakdown_characters = []
    #for sm, (sm, entries, compound_parts) in cedict.items():
        #CEDICT.v

    return breakdown_characters


@task
def get_captions_breakdown_characters(captions):
    breakdown_characters = []
    #let [texts, t0s, t1s, boundingRects, charProbs, logprob, data_hash, translations, alignments] = arr;
    for *_, alignments in captions['lines']:
        #let [startIdx, endIdx, hz, pinyin, wordTranslation] = this.showData.alignments[i];
        for _, _, hz, *_ in alignments:
            if len(filter_text_hanzi(hz)) == 0:
                continue
            if hz not in CEDICT.v:
                breakdown_characters.append(hz)

    return breakdown_characters

