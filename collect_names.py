from merkl import task, pipeline, Eval
from transformer_segmentation import segment_sentences, segmentations_to_pinyin, join_names_present_in_translations


@task
def collect_names(caption_data):
    lines = caption_data['lines']

    all_lines = [' '.join(line[0]) for line in lines]
    all_translations = [line[7] if isinstance(line[7], list) else [line[7]] for line in lines]

    all_confirmed_names = []
    with Eval():
        all_segments = segment_sentences(all_lines, join_compound_words=True)
        all_pys = segmentations_to_pinyin(all_segments)
        all_segments, all_pys, confirmed_names = join_names_present_in_translations(all_segments, all_pys, all_translations)
        all_confirmed_names += confirmed_names

    return all_confirmed_names
