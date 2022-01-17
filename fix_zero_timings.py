import os
import sys
from wrapped_json import json
from predict_video import predict_video_captions
from levenshtein import weighted_levenshtein


def fix_zero_timings_for_videos(
    list_path: str,
    videos_path: str,
    caption_top: float,
    caption_bottom: float,
):
    with open(list_path, 'r') as f:
        video_ids = [vid for vid in f.read().split('\n') if vid.strip() != '']

    all_captions = []
    for video_id in video_ids:
        if video_id.startswith('#'):
            continue

        for fmt in ['mkv', 'webm', 'mp4']:
            video_path = os.path.join(videos_path, video_id + '.' + fmt)
            if os.path.exists(video_path):
                break
        else:
            video_path = None

        if video_path is None:
            print(f'Found no video for id {video_id}')
            continue

        caption_id = f'youtube-{video_id}'
        raw_captions_file = f'data/remote/private/caption_data/raw_captions/{caption_id}.json'
        redo_sections = []
        data = None
        with open(raw_captions_file, 'r') as f:
            data = json.loads(f.read())
            lines = data['lines']

            last_was_redo = False
            for i, (text, t0, t1, rect) in list(enumerate(lines))[1:-1]:
                if t0 == 0 or t1 == 0:
                    prev_line_t0, prev_line_t1 = lines[i-1][1:3]
                    next_line_t0, next_line_t1 = lines[i+1][1:3]

                    prev_line_tm = max(prev_line_t1 - 0.5, prev_line_t0)
                    next_line_tm = min(next_line_t0 + 0.5, next_line_t1)
                    print(prev_line_tm, t0, t1, next_line_tm, text)
                    if last_was_redo:
                        prev_texts, prev_indices = redo_sections[-1][-2:]
                        prev_texts.append(text)
                        prev_indices.append(i)
                        redo_sections[-1] = (redo_sections[-1][0], next_line_tm, prev_texts, prev_indices)
                    else:
                        redo_sections.append((prev_line_tm, next_line_tm, [text], [i]))
                    last_was_redo = True
                else:
                    last_was_redo = False

        print(f'Caption id: {caption_id}')

        for t0, t1, texts, indices in redo_sections:
            print(f't0={t0}, t1={t1}')
            captions, frame_size = predict_video_captions(video_path, caption_top, caption_bottom, t0, t1, replace_levenshtein_threshold=1.0, do_save_caption_data=False)
            captions.cache = None
            captions = captions.eval()

            for text, idx in zip(texts, indices):
                closest_match = None
                closest_match_dist = float('inf')
                for caption in captions:
                    dist = weighted_levenshtein(caption.text, text)
                    if dist < closest_match_dist:
                        closest_match_dist = dist
                        closest_match = caption

                print('==================== MATCH ======================')
                print(closest_match, closest_match_dist)
                if closest_match is not None:
                    data['lines'][idx][1] = closest_match.t0
                    data['lines'][idx][2] = closest_match.t1
                else:
                    if data['lines'][idx][1] == 0 or data['lines'][idx][2] == 0:
                        continue
                    print('Prev', data['lines'][idx])
                    data['lines'][idx][1] = closest_match.t0
                    data['lines'][idx][2] = closest_match.t1
                    print('After', data['lines'][idx])

        for i, line in enumerate(data['lines']):
            _, t0, t1, _ = line
            if t0 == 0:
                data['lines'][i][1] = max(t1 - 1, data['lines'][i-1][2] if i > 0 else 0)
            elif t1 == 0:
                data['lines'][i][2] = min(t0 + 1, data['lines'][i+1][1] if i < len(data['lines']) - 1 else float('inf'))

        with open(raw_captions_file, 'w') as f:
            json.dump(data, f)

    return all_captions
