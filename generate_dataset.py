import os
import sys
import json
import math
import shutil
import random
import subprocess
from math import floor, ceil
from glob import glob
from tempfile import NamedTemporaryFile, mkstemp

import cv2
import numpy as np
from hanziconv import HanziConv
from pymatting import blend

from merkl import pipeline, task, batch, FileRef, DirRef, combine_file_refs


@task(deps=[FileRef('generate_text_images.js')])
def generate_text_image(text, text_width, text_color, font, font_size, line_width, line_color, bold, italic):
    raise NotImplementedError
    return 'image', 'mask', 'text_widths'


def _make_width(img, width):
    left = max(math.floor((img.shape[1] - width) / 2), 0)
    w = min(img.shape[1] - left, width)
    shape = (img.shape[0], width, *img.shape[2:])
    out = np.zeros(shape, img.dtype)
    out[:, :w] = img[:, left:(left+w)]
    return out


def _increase_brightness(img, value=30):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    lim = 255 - value
    v[v > lim] = 255
    v[v <= lim] += value

    final_hsv = cv2.merge((h, s, v))
    img = cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)
    return img

@task
def generate_cutout_composite(cutout_filename, prob_filename, background_filename, out_width, scale=1.0, blur_iterations=0, brighten=False, sample_background_from_cutout=False):
    cutout = cv2.imread(cutout_filename, cv2.IMREAD_UNCHANGED)
    prob = cv2.imread(prob_filename, cv2.IMREAD_GRAYSCALE)

    foreground = cutout[..., :3].astype('float') / 255
    alpha = cutout[..., -1].astype('float') / 255
    alpha = cv2.blur(alpha, (3, 3))
    background = cv2.imread(background_filename)
    if brighten:
        background = _increase_brightness(background, 200)

    background = background.astype('float') / 255

    if sample_background_from_cutout:
        indices_y, indices_x = np.where(alpha > 0.7)
        random_idx = int(random.random() * len(indices_y))
        random_idx_color = foreground[indices_y[random_idx], indices_x[random_idx], :]
        background[..., :] = random_idx_color

    composite = (255 * blend(foreground, background, alpha)).astype('uint8')
    composite = _make_width(composite, out_width)
    if blur_iterations > 0:
        for _ in range(blur_iterations):
            composite = cv2.blur(composite, (3, 3))
    composite_filename = FileRef(ext='jpg')
    cv2.imwrite(composite_filename, composite)

    #cv2.imshow('foreground', cutout[..., :3])
    #cv2.imshow('background', background)
    cv2.imshow('composite', composite)
    #cv2.imshow('alpha', alpha)
    cv2.waitKey(1)

    mask = 255*(prob > 255//2).astype('uint8')
    mask = _make_width(mask, out_width)
    mask_filename = FileRef(ext='png')
    cv2.imwrite(mask_filename, mask)
    return composite_filename, mask_filename


@batch(generate_text_image)
def generate_text_images(args):
    csv_file = FileRef()
    with open(csv_file, 'w') as f:
        for text, text_width, text_color, font, font_size, line_width, line_color, bold, italic in args:
            bold = 'true' if bold else 'false'
            italic = 'true' if italic else 'false'
            font_size = str(font_size)
            line_width = str(line_width)
            text_width = str(text_width)
            f.write(';;'.join([text, text_width, text_color, font, font_size, line_width, line_color, bold, italic]) + '\n')


    dir_out = DirRef()
    text_widths_out = FileRef(ext='csv')
    command = ["node", "generate_text_images.js", csv_file, dir_out, text_widths_out]
    print(' '.join(command))
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    for line in proc.stdout:
        sys.stdout.write(line.decode('utf-8'))

    text_widths = []
    with open(text_widths_out, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            text_widths.append([int(width) for width in line.split(',') if width != ''])

    outs = []
    for i in range(len(args)):
        text_img = FileRef(f'{dir_out}/text_{i}.png', rm_after_caching=True)
        text_mask = FileRef(f'{dir_out}/text_{i}_mask.png', rm_after_caching=True)
        outs.append((text_img, text_mask, text_widths[i]))

    os.remove(csv_file)
    return outs


@task
def render_final_image_and_mask(
        text,
        text_image_path,
        text_mask_path,
        text_widths,
        background_image_path,
        bg_color_hsv,
        bg_alpha,
        blur_bg,
        blur_after_render,
        down_upscale_after_render,
        bg_x_offset_percent,
        bg_y_offset_percent,
        text_x_offset_percent,
        jpeg_quality,
        out_width,
        out_height,
):
    text_img = cv2.imread(text_image_path, cv2.IMREAD_UNCHANGED)
    text_mask = cv2.imread(text_mask_path, cv2.IMREAD_GRAYSCALE)

    text_x, text_y, text_width, text_height = cv2.boundingRect(255*(text_img[..., -1] > 0).astype('uint8'))

    if text_height > out_height:
        print('Text is taller than out_height, skimming off the top')
        text_y += text_height - out_height
        text_height = out_height

    text_img = text_img[text_y:text_y+text_height, text_x:text_x+text_width]
    text_mask = text_mask[text_y:text_y+text_height, text_x:text_x+text_width]

    background = cv2.imread(background_image_path)
    if background.shape[1] < out_width or background.shape[0] < out_height:
        tiles = (
            ceil(out_height / background.shape[0]),
            ceil(out_width / background.shape[1]),
            1
        )
        background = np.tile(background, tiles)

    side = (out_height - text_height) // 2

    bg_y_offset = 10 + floor(bg_y_offset_percent * (background.shape[0] - out_height - 20))
    bg_x_offset = max(0, floor(bg_x_offset_percent * (background.shape[1] - out_width - 20)))

    background_crop = background[bg_y_offset:bg_y_offset+out_height, bg_x_offset:bg_x_offset+out_width, :]
    text_x_offset = max(0, floor(text_x_offset_percent * (out_width - text_width)))
    text_img_crop = text_img[:, :out_width, :3]
    text_alpha_crop = text_img[:, :out_width, -1]
    text_mask_crop = text_mask[:, :out_width]

    text_mask = np.zeros(background_crop.shape[:2], 'uint8')
    text_mask[side:side+text_height, text_x_offset:(text_x_offset+text_width)] = text_mask_crop
    text_img = np.zeros(background_crop.shape, 'uint8')
    text_img[side:side+text_height, text_x_offset:(text_x_offset+text_width)] = text_img_crop
    text_alpha = np.zeros(background_crop.shape[:2], 'uint8')
    text_alpha[side:side+text_height, text_x_offset:(text_x_offset+text_width)] = text_alpha_crop

    if blur_bg:
        # Sometimes, blur the background a lot, because background is often blurry in Chinese dramas
        background_crop = cv2.blur(background_crop, (9, 9))

    if bg_alpha > 0.0:
        bg_overlay_hsv = np.zeros(background_crop.shape, 'uint8')
        bg_overlay_hsv[..., 0] = int(bg_color_hsv[0] / 360 * 180)
        bg_overlay_hsv[..., 1] = int(bg_color_hsv[1] / 100 * 255)
        bg_overlay_hsv[..., 2] = int(bg_color_hsv[2] / 100 * 255)
        bg_overlay_bgr = cv2.cvtColor(bg_overlay_hsv, cv2.COLOR_HSV2BGR)
        background_crop = np.stack([background_crop[..., c] * (1-bg_alpha) + bg_overlay_bgr[..., c] * bg_alpha for c in range(3)], axis=-1)
        background_crop = background_crop.astype('uint8')

    text_alpha = text_alpha.astype('float') / 255
    rendered = np.stack([background_crop[..., c] * (1-text_alpha) + text_img[..., c] * text_alpha for c in range(3)], axis=-1)
    rendered = rendered.astype('uint8')

    if blur_after_render:
        # Sometimes blur the image a bit
        rendered = cv2.blur(rendered, (3, 3))

    if down_upscale_after_render > 1:
        orig_shape = rendered.shape[:2][::-1]
        downscaled = cv2.resize(
            rendered,
            (
                int(orig_shape[0] // down_upscale_after_render),
                int(orig_shape[1] // down_upscale_after_render)
            ),
            interpolation=cv2.INTER_LANCZOS4
        )
        rendered = cv2.resize(downscaled, (*orig_shape,))

    mask = 255*(text_mask > 0.3*255).astype('uint8')
    image_out = FileRef(ext='jpg')
    mask_out = FileRef(ext='png')
    cv2.imwrite(image_out, rendered, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
    cv2.imwrite(mask_out, mask)

    text_positions = []
    for character, from_offset, to_offset in zip(text, text_widths[:-1], text_widths[1:]):
        text_positions.append((character, from_offset + text_x_offset, to_offset + text_x_offset))
        x1 = (from_offset + text_x_offset, 0)
        x2 = (to_offset + text_x_offset, rendered.shape[0])
        cv2.rectangle(rendered, x1, x2, (255, 255, 255), 3)

    #cv2.imshow('text_positions', rendered)
    #cv2.waitKey()

    return image_out, mask_out, text_positions


def random_hsv_str():
    H = floor(random.random() * 360)
    S = floor(random.random() * 100)
    L = 70 + floor(random.random() * 30)
    a = 0.8 if random.random() < 0.05 else 1.0
    return f'hsla({H}, {S}%, {L}%, {a})'


@task
def combine(arg):
    return arg


@pipeline
def pipeline(corpus: list, num: int, out_width: int, out_height: int, seed: int = 42, fill_with_synthetic=True):
    random.seed(seed+1)

    print('Generating composites')
    CAPTION_DATA_DIR = 'data/remote/private/caption_data'
    composite_images = []
    composite_masks = []
    composite_text_positions = []
    for show_name in os.listdir(f'{CAPTION_DATA_DIR}/cutouts'):
        if show_name.endswith('.json'):
            continue

        with open(f'{CAPTION_DATA_DIR}/cutouts/{show_name}.json', 'r') as f:
            empty_line_hashes = json.load(f)

        show_dir = f'{CAPTION_DATA_DIR}/cutouts/{show_name}'
        for cutout in os.listdir(show_dir):
            cutout_hash = cutout.split('.')[0]
            cutout_filename = f'{show_dir}/{cutout}'

            for i in range(10):
                j = int(random.random() * len(empty_line_hashes))
                hash = empty_line_hashes[j]
                background_filename = FileRef(f'{CAPTION_DATA_DIR}/images/{hash}.jpg')
                if not os.path.exists(background_filename):
                    print('Background', background_filename, 'does not exist')
                    continue

                prob_filename = FileRef(f'{CAPTION_DATA_DIR}/segmentation_probs/{cutout_hash}.png')
                composite, mask = generate_cutout_composite(
                    cutout_filename,
                    prob_filename,
                    background_filename,
                    out_width,
                    blur_iterations=round(1+random.random()*1) if random.random() < 0.4 else 0,
                    scale=1.0,
                    sample_background_from_cutout=(i <= 4),
                    brighten=(i <= 7),
                )
                composite_images.append(composite)
                composite_masks.append(mask)
                composite_text_positions.append(None)

    # Make sure the total number of images out is `num`
    num -= len(composite_images)

    if fill_with_synthetic:
        random.seed(seed)  # seed again so changes above do not affect the generation below

        print('reading weibo dataset')
        fonts = [path.split('.')[0] for path in os.listdir('data/remote/private/fonts/')]

        print('generating text image parameters')
        text_image_parameters = []
        for text in corpus[:num]:
            text = HanziConv.toTraditional(text) if random.random() < 0.5 else text
            font = random.choice(fonts)
            color = random_hsv_str()
            font_size = 58 + floor(random.random() * 5)
            text_width = max(floor(out_width * random.random()), 2*font_size + 1)
            bold = random.random() < 0.5
            italic = False
            line_width = floor(random.random() * 6)
            line_color = 'black'
            text_image_parameters.append((text, text_width, color, font, font_size, line_width, line_color, bold, italic))

        print('calling generate_text_images')
        text_image_paths = generate_text_images(text_image_parameters)
        print('done')

        background_image_paths = [FileRef(path) for path in glob('data/remote/private/backgrounds/*')]

        random.seed(seed)  # reset seed, so randomizing here is not affected by previous randomization
        render_image_paths = []
        render_mask_paths = []
        render_text_positions = []
        for (text_image_path, text_mask_path, text_widths), params in zip(text_image_paths, text_image_parameters):
            text = params[0]
            background_image_path = random.choice(background_image_paths)
            blur_background = random.random() < 0.3
            blur_after_render = random.random() < 0.1
            down_upscale_after_render = 1
            if random.random() < 0.05:
                r = random.random()
                if r < 0.33:
                    down_upscale_after_render = 1.25
                elif r < 0.66:
                    down_upscale_after_render = 1.5
                else:
                    down_upscale_after_render = 1.8

            bg_x_offset_percent = random.random()
            bg_y_offset_percent = random.random()
            text_x_offset_percent = random.random()
            jpeg_quality = 30 if random.random() < 0.1 else 100
            bg_color_hsv = (
                floor(random.random() * 360),
                floor(random.random() * 100),
                floor(random.random() * 50),
            )
            if random.random() < 0.4:
                bg_color_hsv = (0, 0, 0)  # black

            bg_alpha = 0.0
            if random.random() < 0.05:
                bg_alpha = 1.0 if random.random() < 0.5 else random.random()

            img, mask, text_positions = render_final_image_and_mask(
                text,
                text_image_path,
                text_mask_path,
                text_widths,
                background_image_path,
                bg_color_hsv,
                bg_alpha,
                blur_background,
                blur_after_render,
                down_upscale_after_render,
                bg_x_offset_percent,
                bg_y_offset_percent,
                text_x_offset_percent,
                jpeg_quality,
                out_width,
                out_height,
            )
            render_image_paths.append(img)
            render_mask_paths.append(mask)
            render_text_positions.append(text_positions)


        composite_images += render_image_paths
        composite_masks += render_mask_paths
        composite_text_positions += render_text_positions

    render_images_dir = combine_file_refs(composite_images)
    render_masks_dir = combine_file_refs(composite_masks)
    return render_images_dir, render_masks_dir, combine(composite_text_positions)
