import os
import sys
import math
import shutil
import argparse

import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image
from pymatting import cutout, blend

from wrapped_json import json

parser = argparse.ArgumentParser(description='Fix raw caption errors')
parser.add_argument('filename', type=str)
parser.add_argument('--show', type=str, default='')
parser.add_argument('--keys', action='store_true')
parser.add_argument('--num', type=int, default=30)
parser.add_argument('--dilate-foreground', type=int, default=2)
parser.add_argument('--dilate-move-foreground', type=str, default='')
parser.add_argument('--erode-foreground', type=int, default=0)
parser.add_argument('--dilate-unknown', type=int, default=3)

args = parser.parse_args()

keys = {
    'e': 'edit',
    'j': 'join lines',
    's': 'save edited raw captions',
    'backspace': 'prev',
    'space': 'next',
    'd': 'half page next',
    'u': 'half page prev',
    'g': 'save good example'
}


if args.keys:
    print('Keys:')
    for key, desc in keys.items():
        print(key, ': ', desc)
    sys.exit()

orig_filename = args.filename[:-5] + '-orig.json'

if not os.path.exists(orig_filename):
    shutil.copy(args.filename, orig_filename)
    print('Made copy to ', orig_filename)

with open(args.filename, 'r') as f:
    raw_captions = json.load(f)

lines = raw_captions['lines']

curr_show_idx = 0

CAPTION_DATA_DIR = 'data/remote/private/caption_data'
INPUT_HEIGHT = 80
SCALE_FACTOR = 2
LINE_HEIGHT = INPUT_HEIGHT // SCALE_FACTOR
LINE_WIDTH_BUFFER = 5
FONT_PATH = "./data/remote/private/fonts/fangzhengheiti.ttf"
FONT_BUFFER = 20
FONT = ImageFont.truetype(FONT_PATH, (INPUT_HEIGHT-2*FONT_BUFFER) // SCALE_FACTOR)
img_path = '/tmp/cutout_img.png'
trimap_path = '/tmp/cutout_trimap.png'
out_path = '/tmp/cutout_out.png'
cutout_dir = f'{CAPTION_DATA_DIR}/cutouts/{args.show}/'
os.makedirs(cutout_dir, exist_ok=True)

selected_indices = set()

if args.show != '':
    empty_hashes = []
    show_file = f'{CAPTION_DATA_DIR}/cutouts/{args.show}.json'
    if os.path.exists(show_file):
        with open(show_file, 'r') as f:
            print('Read current background hashes file')
            empty_hashes = json.load(f)

    for line in lines:
        if line[0] == '' and os.path.exists(f'{CAPTION_DATA_DIR}/images/{line[-1]}.jpg'):
            empty_hashes.append(line[-1])
    with open(show_file, 'w') as f:
        print('Writing background hashes file')
        json.dump(list(set(empty_hashes)), f)

def draw_frame():
    height = args.num * LINE_HEIGHT
    img_buffer = None
    min_x = float('inf')
    max_x = 0

    for _, _, _, rect, *_ in lines[curr_show_idx:curr_show_idx+args.num]:
        if rect is None:
            continue
        min_x = min(min_x, rect[0])
        max_x = max(max_x, rect[1])

    frame_width = raw_captions['frame_size'][1]
    min_x /= frame_width
    max_x /= frame_width

    for i, line in enumerate(lines[curr_show_idx:curr_show_idx+args.num]):
        hash = line[-1]
        img = cv2.imread(f'{CAPTION_DATA_DIR}/images/{hash}.jpg')
        seg = cv2.imread(f'{CAPTION_DATA_DIR}/segmentation_probs/{hash}.png')
        if img is None:
            continue
        if seg is None:
            seg = np.zeros_like(img)

        max_x_px = math.floor(max_x * img.shape[1])
        min_x_px = math.floor(min_x * img.shape[1])
        img = img[:, min_x_px-LINE_WIDTH_BUFFER:max_x_px+LINE_WIDTH_BUFFER, :]
        seg = seg[:, min_x_px-LINE_WIDTH_BUFFER:max_x_px+LINE_WIDTH_BUFFER, :]

        img = cv2.resize(img, (img.shape[1] // SCALE_FACTOR, img.shape[0] // SCALE_FACTOR))
        seg = cv2.resize(seg, (seg.shape[1] // SCALE_FACTOR, seg.shape[0] // SCALE_FACTOR))

        line_width = img.shape[1]

        if img_buffer is None:
            img_buffer = np.zeros((height, 3*line_width, 3), 'uint8')
        else:
            if 3*line_width != img_buffer.shape[1]:
                print('Skipping line', i, hash, 'because image width is different')
                continue

        color = 0
        if i in selected_indices:
            color = 100
        text_img = color * np.ones_like(img)
        img_pil = Image.fromarray(text_img)
        draw = ImageDraw.Draw(img_pil)
        draw.text((FONT_BUFFER//2, FONT_BUFFER//2), line[0], font=FONT, fill=(255, 255, 255, 0))
        text_img = np.array(img_pil)

        for j, draw_img in enumerate([text_img, img, seg]):
            img_buffer[i*LINE_HEIGHT:(i+1)*LINE_HEIGHT, (j*line_width):((j+1)*line_width)] = draw_img

    if img_buffer is not None:
        cv2.imshow('img', img_buffer)


def handle_click(event,x,y,flags,param):
    #print(event)
    if event == cv2.EVENT_LBUTTONDOWN:
        idx = y // (INPUT_HEIGHT // SCALE_FACTOR)
        print('clicked idx', idx)
        if idx in selected_indices:
            selected_indices.remove(idx)
        else:
            selected_indices.add(idx)
        draw_frame()
        cv2.waitKey(1)

cv2.namedWindow('img')
cv2.setMouseCallback('img', handle_click)

import readline

def rlinput(prompt, prefill=''):
   readline.set_startup_hook(lambda: readline.insert_text(prefill))
   try:
      return input(prompt)  # or raw_input in Python 2
   finally:
      readline.set_startup_hook()

while True:
    draw_frame()
    key = cv2.waitKey()
    print('key', key)
    if key == ord('e'):
        if len(selected_indices) == 1:
            idx = selected_indices.pop()
            line = lines[idx + curr_show_idx]
            edited_text = rlinput('Edit: ', prefill=line[0])
            line[0] = edited_text
            line[4] = None  # char probs
            line[5] = 0  # logprob
    elif key == ord('j'):
        if len(selected_indices) > 1:
            sorted_indices = sorted(list(selected_indices))
            selected_lines = [lines[idx + curr_show_idx] for idx in sorted_indices]
            for i, line in enumerate(selected_lines):
                print(f'{i}. {line[0]}')
            correct = input('Select most correct text index: ')
            correct = int(correct)
            correct_line = selected_lines[correct]

            edited_text = rlinput('Edit: ', prefill=correct_line[0])
            correct_line[0] = edited_text

            t0 = selected_lines[0][1]
            t1 = selected_lines[-1][2]
            correct_line[1] = t0
            correct_line[2] = t1
            correct_line[4] = None  # char probs
            correct_line[5] = 0  # logprob
            print('Final line', correct_line)

            # Replace the first line with the correct line, and pop all the other discarded lines
            lines[sorted_indices[0] + curr_show_idx] = correct_line
            for idx in reversed(sorted_indices[1:]):
                popped = lines.pop(idx + curr_show_idx)
                print('Popped', idx + curr_show_idx, popped)

        selected_indices = set()
    elif key == ord('s'):
        with open(args.filename, 'w') as f:
            json.dump(raw_captions, f)
        print('Saved to ', args.filename)
    elif key == ord('u'):
        selected_indices = set()
        curr_show_idx = max(0, curr_show_idx - args.num // 2)
    elif key == 8:  # backspace
        selected_indices = set()
        curr_show_idx = max(0, curr_show_idx - args.num)
    elif key == ord('d'):
        selected_indices = set()
        curr_show_idx = min(curr_show_idx + args.num // 2, len(lines) - 1)
    elif key == 32:  # space
        selected_indices = set()
        curr_show_idx = min(curr_show_idx + args.num, len(lines) - 1)
    elif key == ord('g'):
        if args.show == '':
            print('ERROR: need to set --show name for saving good examples')
            sys.exit(1)

        for idx in selected_indices:
            idx = idx + curr_show_idx
            line = lines[idx]
            hash = line[-1]
            seg_prob_file = f'{CAPTION_DATA_DIR}/segmentation_probs/{hash}.png'
            img_file = f'{CAPTION_DATA_DIR}/images/{hash}.jpg'
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


            white_background = np.ones_like(foreground_img, 'float')
            black_background = np.zeros_like(foreground_img, 'float')
            blend_white = (255 * blend(foreground_img, white_background, alpha)).astype('uint8')
            blend_black = (255 * blend(foreground_img, black_background, alpha)).astype('uint8')

            cv2.imshow("blend black", blend_black)
            cv2.imshow("blend white", blend_white)

            save_path = f'{cutout_dir}{hash}.png'
            print('Saving to', save_path)
            cv2.imwrite(save_path, cutout_img)
            cv2.waitKey(1)
