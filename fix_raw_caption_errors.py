import os
import sys
import math
import shutil
import argparse

import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image

from wrapped_json import json

parser = argparse.ArgumentParser(description='Fix raw caption errors')
parser.add_argument('filename', type=str)
parser.add_argument('--num', type=int, default=30)

args = parser.parse_args()

orig_filename = args.filename[:-5] + '-orig.json'

if not os.path.exists(orig_filename):
    shutil.copy(args.filename, orig_filename)
    print('Made copy to ', orig_filename)

with open(args.filename, 'r') as f:
    raw_captions = json.load(f)

lines = raw_captions['lines']

curr_show_idx = 0

INPUT_HEIGHT = 80
SCALE_FACTOR = 2
LINE_HEIGHT = INPUT_HEIGHT // SCALE_FACTOR
LINE_WIDTH_BUFFER = 5
FONT_PATH = "./data/remote/private/fonts/fangzhengheiti.ttf"
FONT_BUFFER = 20
FONT = ImageFont.truetype(FONT_PATH, (INPUT_HEIGHT-2*FONT_BUFFER) // SCALE_FACTOR)

selected_indices = set()

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
        img = cv2.imread(f'data/remote/private/caption_data/images/{hash}.jpg')
        seg = cv2.imread(f'data/remote/private/caption_data/segmentation_probs/{hash}.png')
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
