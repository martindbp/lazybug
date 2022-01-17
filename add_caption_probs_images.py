import os
import sys
import uuid
from wrapped_json import json
import hashlib
import pickle

import numpy as np
import cv2

import predict_video
from predict_video import predict_video_captions, predict_line, get_video_caption_area
from levenshtein import weighted_levenshtein


def add_probs_images_to_captions(
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
        print('Processing', caption_id)
        raw_captions_file = f'data/remote/private/caption_data/raw_captions/{caption_id}.json'
        redo_sections = []
        data = None
        with open(raw_captions_file, 'r') as f:
            data = json.loads(f.read())
            lines = data['lines']
            if len(lines[0]) > 4:
                continue  # this video has already been processed

            for i, (text, t0, t1, rect) in enumerate(lines):
                t = (t0 + t1) / 2
                caption_images = get_video_caption_area(
                    video_path, caption_top, caption_bottom, t, t, 80, 60
                )
                mid_img = list(caption_images)[0][1]
                pred_caption = predict_line(mid_img, t)

                if pred_caption.text != text:
                    # Redo the whole section
                    prev_line_t0, prev_line_t1 = None, None
                    if i > 0:
                        prev_line_t0, prev_line_t1 = lines[i-1][1:3]

                    next_line_t0, next_line_t1 = None, None
                    if i < len(lines) - 1:
                        next_line_t0, next_line_t1 = lines[i+1][1:3]

                    prev_line_tm = max(prev_line_t1 - 0.5, prev_line_t0) if prev_line_t0 is not None else max(0, t - 1)
                    next_line_tm = min(next_line_t0 + 0.5, next_line_t1) if next_line_t0 is not None else t + 1

                    captions, frame_size = predict_video_captions(
                        video_path, caption_top, caption_bottom, prev_line_tm, next_line_tm,
                        replace_levenshtein_threshold=1.0, zero_out_numpy=False, do_save_caption_data=False,
                    )
                    captions.cache = None
                    captions = captions.eval()

                    closest_match = None
                    closest_match_dist = float('inf')
                    for caption in captions:
                        dist = weighted_levenshtein(caption.text, text)
                        if dist < closest_match_dist:
                            closest_match_dist = dist
                            closest_match = caption

                    pred_caption = closest_match
                    print('Searched video')
                else:
                    print('Found directly')

                if pred_caption is None or pred_caption.char_probs is None:
                    lines[i].append(None)
                    lines[i].append(None)
                    lines[i].append(None)
                    continue
                    
                h = hashlib.md5()
                h.update(bytes(text, 'utf-8'))
                h.update(bytes(str(t0), 'utf-8'))
                h.update(bytes(str(t1), 'utf-8'))
                data_hash = h.hexdigest()
                breakpoint()
                lines[i].append([float(prob) for prob in pred_caption.char_probs])
                lines[i].append(float(pred_caption.logprob))
                lines[i].append(data_hash)

                top10_char_probs = []
                for prob_distribution in pred_caption.prob_distributions:
                    top10_indices = np.argpartition(prob_distribution, -10)[-10:]
                    top10_probs = [float(p) for p in prob_distribution[top10_indices]]
                    top10_chars = [predict_video.ocr._alphabet[idx] for idx in top10_indices]
                    top10_char_probs.append(list(sorted(zip(top10_chars, top10_probs), key=lambda x: x[1], reverse=True)))

                img_path = f'data/remote/private/caption_data/images/{data_hash}.jpg'
                caption_probs_path = f'data/remote/private/caption_data/segmentation_probs/{data_hash}.png'
                prob_distributions_path = f'data/remote/private/caption_data/char_probability_distributions/{data_hash}.pickle'
                cv2.imwrite(img_path, pred_caption.img, [cv2.IMWRITE_JPEG_QUALITY, 90])
                cv2.imwrite(caption_probs_path, (pred_caption.probs * 255).astype('uint8'))
                with open(prob_distributions_path, 'wb') as f:
                    pickle.dump(top10_char_probs, f)
                
        with open(raw_captions_file, 'w') as f:
            json.dump(data, f)

    return all_captions
