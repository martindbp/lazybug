import os
import cv2
import sys
import json
import shutil
import numpy as np
from pymatting import cutout, blend

import argparse

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('show_name', type=str)
parser.add_argument('--dilate-foreground', type=int, default=2)
parser.add_argument('--dilate-move-foreground', type=str, default='')
parser.add_argument('--erode-foreground', type=int, default=0)
parser.add_argument('--dilate-unknown', type=int, default=3)
parser.add_argument('--overwrite', action='store_true')
parser.add_argument('--skip', action='store_true')

args = parser.parse_args()

CAPTION_DATA_DIR = 'data/remote/private/caption_data'
img_path = '/tmp/cutout_img.png'
trimap_path = '/tmp/cutout_trimap.png'
out_path = '/tmp/cutout_out.png'

with open(f'data/remote/private/shows/{args.show_name}.json', 'r') as f:
    show_json = json.load(f)

files = []
for season in show_json['seasons']:
    for video in season['episodes']:
        filename = f'{CAPTION_DATA_DIR}/raw_captions/{video["id"]}-hanzi.json'
        files.append(filename)

cutout_dir = f'{CAPTION_DATA_DIR}/cutouts/{args.show_name}/'
os.makedirs(cutout_dir, exist_ok=True)

empty_hashes = []
for filename in files:
    with open(filename, 'r') as f:
        data = json.load(f)

    for line in data['lines']:
        if line[0] == '' and os.path.exists(f'{CAPTION_DATA_DIR}/images/{line[-1]}.jpg'):
            empty_hashes.append(line[-1])

with open(f'{CAPTION_DATA_DIR}/cutouts/{args.show_name}.json', 'w') as f:
    json.dump(empty_hashes, f)

for filename in files:
    with open(filename, 'r') as f:
        data = json.load(f)

    last_empty = None
    for line in data['lines']:
        print(line)
        hash = line[-1]

        seg_prob_file = f'{CAPTION_DATA_DIR}/segmentation_probs/{hash}.png'
        img_file = f'{CAPTION_DATA_DIR}/images/{hash}.jpg'
        save_path = f'{cutout_dir}{hash}.png'
        exists = os.path.exists(save_path)
        if exists and not args.overwrite:
            print('Save path', save_path, 'already exists')
            continue

        seg = cv2.imread(seg_prob_file, cv2.IMREAD_GRAYSCALE)
        img = cv2.imread(img_file)
        if seg is None:
            last_empty = line
            continue

        foreground = 255*(seg > 255/2).astype('uint8')

        if args.dilate_foreground > 0:
            foreground = cv2.dilate(foreground, np.ones((3, 3), np.uint8), iterations=args.dilate_foreground)

        if args.erode_foreground > 0:
            foreground = cv2.erode(foreground, np.ones((3, 3), np.uint8), iterations=args.dilate_foreground)

        if args.dilate_move_foreground:
            dy, dx = args.dilate_move_foreground.split(',')
            dy, dx = int(dy), int(dx)
            foreground = foreground | np.roll(foreground.copy(), (dy, dx), axis=(0, 1))

        if args.dilate_unknown > 0:
            unknown = cv2.dilate(foreground.copy(), np.ones((3, 3), np.uint8), iterations=args.dilate_unknown)
            unknown = unknown & ~foreground
        
            trimap = foreground.copy()
            trimap[unknown > 0] = 255 // 2

            img_plus_trimap = img.copy()
            img_plus_trimap[..., -1] = trimap
            cv2.imshow('img_plus_trimap', img_plus_trimap)

            cv2.imwrite(img_path, img)
            cv2.imwrite(trimap_path, trimap)
            cutout(img_path, trimap_path, out_path)
            cutout_img = cv2.imread(out_path, cv2.IMREAD_UNCHANGED)
            foreground_img = cutout_img[..., :3].astype('float') / 255
            alpha = cutout_img[..., -1].astype('float') / 255
            alpha = cv2.blur(alpha, (3, 3))
            cv2.imshow('cutout_img', cutout_img)
        else:
            alpha = seg.astype('float') / 255
            foreground_img = img.astype('float') / 255
            cutout_img = np.dstack((img, seg))

        if last_empty is not None:
            background = cv2.imread(f'{CAPTION_DATA_DIR}/images/{last_empty[-1]}.jpg')
            if background is not None:
                background = background.astype('float') / 255
                new_image = (255 * blend(foreground_img, background, alpha)).astype('uint8')
                cv2.imshow('alpha', alpha)
                cv2.imshow('foreground', foreground)
                cv2.imshow('blended', new_image)
                cv2.imshow('segprobs', seg)
                cv2.imshow('foreground_img', foreground_img)
                cv2.imshow('img', img)

        if not exists and not args.skip:
            key = cv2.waitKey()

            if key == ord('s'):
                print('Saving to', save_path)
                cv2.imwrite(save_path, cutout_img)
                #shutil.move(out_path, f'{cutout_dir}{hash}.png')
        elif exists and args.overwrite:
            print('Overwriting', save_path)
            cv2.imwrite(save_path, cutout_img)
