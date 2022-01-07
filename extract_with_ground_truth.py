import sys
import json
from pathlib import Path

import cv2
import numpy as np

from train_predict import predict_pipeline

OUT_SIZE = 80
FONT_HEIGHT = 60

video_path = sys.argv[1]
captions_path = sys.argv[2]
output_path = sys.argv[3]
caption_top = int(sys.argv[4])
caption_bottom = int(sys.argv[5])

with open(captions_path, 'r') as f:
    captions = json.loads(f.read())


def predict_chars(mask, window_buffer=10):
    if mask.sum() == 0:
        return ''
    ys, xs = np.where(mask > 0)
    x_max, x_min = xs.max()+1, xs.min()
    y_max, y_min = ys.max()+1, ys.min()
    mask_crop = mask[y_min:y_max, x_min:x_max]

    larger = np.zeros((mask_crop.shape[0]+2*window_buffer, mask_crop.shape[1]+2*window_buffer), 'uint8')
    larger[window_buffer:-window_buffer, window_buffer:-window_buffer] = mask_crop
    larger = 255 - larger
    res = ocr.ocr_for_single_line(larger)
    return ''.join(res)


cap = cv2.VideoCapture(video_path)

i = 0
for caption in captions['events']:
    start = caption['tStartMs']
    end = start + caption['dDurationMs']
    text = caption['segs'][0]['utf8']
    if len(caption['segs']) > 1:
        print('WARNING: More than one seg:', caption)

    print(text)

    cap.set(cv2.CAP_PROP_POS_MSEC, (start+end) // 2)
    _, frame = cap.read()

    scale_factor = FONT_HEIGHT / (caption_bottom - caption_top)
    resized = cv2.resize(frame, (int(frame.shape[1] * scale_factor), int(frame.shape[0] * scale_factor)), interpolation=cv2.INTER_LANCZOS4)
    top_resized = int(caption_top * scale_factor)
    bottom_resized = int(caption_bottom * scale_factor)

    padding = (OUT_SIZE - FONT_HEIGHT) // 2
    crop = resized[top_resized-padding:bottom_resized+padding, :]
    assert crop.shape[0] == OUT_SIZE

    crop_path = str(Path(output_path) / f'{i}.jpg')
    cv2.imwrite(crop_path, crop)
    #mask, probs = predict_pipeline(crop_path)


    cv2.imshow('crop', crop)
    cv2.imshow('full', frame)
    #cv2.imshow('mask', mask.eval())
    cv2.waitKey()

    i += 1

cap.release()
