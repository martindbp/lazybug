from misc import transfer_punctuation
from levenshtein import weighted_levenshtein, OpType


def make_caption_lines_lists(caption_lines):
    # First convert all the properties into lists, so that we can merge lines
    for line in caption_lines:
        if not isinstance(line[0], list):
            # We're merging, so turn data into lists
            for i in range(0, 7):
                line[i] = [line[i]]

BAD_OVERLAP_THRESHOLD = 0.5 # seconds

def align_translations_and_captions(caption_data, translations, remove_unmatched_captions=True):
    """
    NOTE: updates the caption_data by appending the translation at the appropriate caption.
    Also transfers punctuation marks from the human translation to the caption
    """
    caption_lines = caption_data['lines']
    translation_lines = translations['lines']
    # NOTE: Translations from Youtube may not line up very well with the actual captions, some might not even intersect
    # in time, so do a fuzzy match based on intersections

    def _subst_cost(translation, caption, i, j):
        caption_t0, caption_t1 = caption[1][0], caption[2][-1]
        translation_t0, translation_t1 = translation[1], translation[2]
        intersection_start = max(caption_t0, translation_t0)
        intersection_end = min(caption_t1, translation_t1)
        if intersection_end < intersection_start:
            return 1.0 + (intersection_start - intersection_end) if intersection_start - intersection_end > BAD_OVERLAP_THRESHOLD else 1.0

        # Return 0.0 if intersection is perfect, otherwise the inverse of the intersection percentage
        non_intersection = 1.0 - (intersection_end - intersection_start) / max(0.01, (caption_t1 - caption_t0))
        assert(non_intersection >= 0 and non_intersection <= 1)
        return non_intersection

    def _insert_cost(caption, i):
        caption_t0, caption_t1 = caption[1][0], caption[2][-1]
        nonlocal translation_lines
        if i >= len(translation_lines):
            return 1.0
        translation = translation_lines[i]

        translation_t0, translation_t1 = translation[1], translation[2]
        intersection_start = max(caption_t0, translation_t0)
        intersection_end = min(caption_t1, translation_t1)
        if intersection_end < intersection_start:
            return 1.0 + (intersection_start - intersection_end) if intersection_start - intersection_end > BAD_OVERLAP_THRESHOLD else 1.0

        # Return 0.0 if intersection is perfect, otherwise the inverse of the intersection percentage
        non_intersection = 1.0 - (intersection_end - intersection_start) / max(0.01, (caption_t1 - caption_t0))
        assert(non_intersection >= 0 and non_intersection <= 1)
        return non_intersection

    dist, ops = weighted_levenshtein(translation_lines, caption_lines, _subst_cost, _insert_cost, return_ops=True)
    for op in ops:
        print(op)

    aligned_translations = []
    # OpType.DELETE means deleting a translation, because there's no matching caption line
    # OpType.INSERT means inserting an (empty) translation, because we have multiple captions for one translation

    for op in ops:
        if op.type == OpType.SUBSTITUTE:
            if op.delta <= 1.0:
                aligned_translations.append([translation_lines[op.from_idx][0]])
            else:
                # If we're substituting with a > 1 distance, it's a bad match
                aligned_translations.append(False)
        elif op.type == OpType.DELETE:
            print('Deleted  ', translation_lines[op.from_idx])
            pass
            """
            if len(aligned_translations) > 0:
                if isinstance(aligned_translations[-1], bool):
                    aligned_translations[-1] = [translation_lines[op.from_idx][0]]
                else:
                    aligned_translations[-1].append(translation_lines[op.from_idx][0])
            else:
                # If deleting at the beginning, it's probably unrelated to captions
                pass
            """
        elif op.type == OpType.INSERT:
            # By appending True, we indicate that captions should be merged, if False then we should discard the caption
            # (it got a high cost, probably because it's not overlapping with the translation)
            print(op.delta)
            if op.delta >= 1.0 + BAD_OVERLAP_THRESHOLD:
                aligned_translations.append(False)
            else:
                aligned_translations.append(True)

    i = 0
    while i < len(caption_data['lines']):
        caption = caption_data['lines'][i]
        translations = aligned_translations[i]
        if translations is True and i > 0:
            # We should merge this caption with the next
            prev_caption = caption_lines[i-1]
            print(f'Merging {prev_caption[0]} + {caption[0]}: {aligned_translations[i-1]}  {caption[2]} {prev_caption[1]}')
            # Prepend the prev_caption data
            for j in range(len(prev_caption)):
                for item in reversed(prev_caption[j]):
                    caption[j].insert(0, item)

            caption_data['lines'].pop(i-1)
            aligned_translations.pop(i)
        elif translations is False:
            if remove_unmatched_captions:
                print(f"Discarding {caption_data['lines'][i]}")
                caption_data['lines'].pop(i)
                aligned_translations.pop(i)
            else:
                print(f"No translation for {caption_data['lines'][i]}, keeping empty")
                i += 1
        else:
            i += 1

    if len(aligned_translations) > 0 and isinstance(aligned_translations[0], bool):
        # Remove first line
        caption_lines.pop(0)
        aligned_translations.pop(0)

    for i, (caption, translations) in enumerate(zip(caption_lines, aligned_translations)):
        if translations == False:
            # There was no matching translation, so we set it to None, and fill it in with machine translation later
            caption.append([])
            continue

        translation = translations[0]  # any extra translations that were added did not have any matching captions
        if len(translations) > 1:
            print('Ignoring these translations:', translations[1:])

        last_caption_text = caption[0][-1]
        last_caption_text = transfer_punctuation(translation, last_caption_text)
        caption[0][-1] = last_caption_text

        print(caption[0], translation)
        caption.append([translation])

    return aligned_translations
