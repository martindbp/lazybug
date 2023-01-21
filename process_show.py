import os
import re
import sys
import math
import glob
import hashlib
import pickle
from dataclasses import dataclass, field
from collections import defaultdict
from functools import partial

import cv2
import numpy as np

import mxnet as mx
from cnocr import CnOcr
from cnocr.fit.ctc_metrics import CtcMetrics
from hanziconv import HanziConv
import torch
from torch.nn import functional as F
import webvtt

os.environ["TRANSFORMERS_CACHE"] = "./data/local/huggingface-models/"
#os.environ["TRANSFORMERS_OFFLINE"] = "1"
from transformers import AutoTokenizer, AutoModelForMaskedLM
from easyocr import Reader

from merkl import task, pipeline, HashMode, FileRef, Future
from wrapped_json import json
from train_predict import predict_img_pipeline, _get_latest_net
from process_translations import get_alignment_translations, get_machine_translations
from word_alignment import add_segmentation_and_alignment
from caption_translation_alignment import align_translations_and_captions, make_caption_lines_lists
from han import filter_text_hanzi, make_cedict
from pinyin import normalized_to_diacritical, extract_normalized_pinyin
from levenshtein import weighted_levenshtein, OpType

from pinyin_freq_db import make_pinyin_freq_db
from pinyin_classifiers import train_pinyin_classifiers
from collect_names import collect_names

DEBUG = False

easy_ocrs = None
tokenizer = None
model = None

HIGH_PROB_CHAR = 0.90


def write_hash_file(filename, hash):
    with open(filename, 'w') as f:
        f.write(hash)


@dataclass
class CaptionLine:
    text: str
    t0: float
    t1: float
    logprob: float
    img: np.array = field(repr=False)
    mask: np.array = field(repr=False)
    probs: np.array = field(repr=False)
    char_probs: np.array = field(repr=False)
    prob_distributions: np.array = field(repr=False)
    bounding_rect: tuple = field(repr=False, default=())
    mean_dist: float = field(repr=False, default=0)
    data_hash: str = field(repr=False, default='')
    conditional_caption_idx: int = field(repr=False, default=None)

    def zero_out_numpy(self):
        # NOTE: we don't zero out char_probs because it's relatively small and we need to save it to json
        self.img, self.mask, self.probs, self.prob_distributions = None, None, None, None


def srt_timestamp(t):
    hours = int(t // (60*60))
    t -= hours * 60 * 60
    minutes = int(t // 60)
    t -= minutes * 60
    seconds = t
    return f'{hours:02}:{minutes:02}:{seconds:.3f}'.replace('.', ',')


@task
def caption_lines_to_srt(lines):
    srt_out = ''
    for i, line in enumerate(lines):
        srt_out += f'{i}\n'
        srt_out += f'{srt_timestamp(line.t0)} --> {srt_timestamp(line.t1)}\n'
        srt_out += f'{line.text}\n\n'

    return srt_out


def _join_predictions(results, alphabet, convert_to_simplified=True):
    if len(results) == 0:
        return None, '', 0, np.array([]), np.array([])
    else:
        results = [x for x in results if len(x[1]) > 0]  # only non-empty predictions
        if len(results) == 0:
            return None, '', 0, np.array([]), np.array([])

        results = sorted(results, key=lambda x: x[0][0][0]) # sort by x value of upper-left corner
        ul = [min(x for ((x, _), *_), *_ in results), min(y for ((_, y), *_), *_ in results)]
        ur = [max(x for (_, (x, _), *_), *_ in results), min(y for (_, (_, y), *_), *_ in results)]
        dr = [max(x for (_, _, (x, _), _), *_ in results), max(y for (_, _, (_, y), _), *_ in results)]
        dl = [min(x for (*_, (x, _)), *_ in results), max(y for (*_, (_, y)), *_ in results)]
        rect = [ul, ur, dr, dl]

        results_with_spaces = []
        for res in results:
            if len(results_with_spaces) > 0:
                indices = np.array([alphabet.index(' ')])
                probs = np.zeros((1, res[4].shape[1]), float)
                probs[0, indices[0]] = 1.0
                results_with_spaces.append((None, ' ', 1.0, indices, probs))

            res = (*res[:3], res[3].numpy(), *res[4:])
            results_with_spaces.append(res)

        text = ''.join((x[1] for x in results_with_spaces))
        mean_confidence_score = np.array([x[2] for x in results_with_spaces]).mean()

        indices = np.concatenate([x[3] for x in results_with_spaces])
        probs = np.concatenate([x[4] for x in results_with_spaces], axis=0)

        if convert_to_simplified:
            # We convert any traditional chars to simplified in text, update the vocab indices, and the probs
            text = HanziConv.toSimplified(text)
            for i, c in enumerate(text):
                simp_idx = alphabet.index(c)
                indices[i] = simp_idx

            # We set prob(simplified(char)) = prob(char) + prob(simplified(char)) for all chars in the alphabet, and set prob(char) to 0
            for i in range(probs.shape[0]):
                for c in alphabet:
                    c_simp = HanziConv.toSimplified(c)
                    if c_simp != c and c_simp in alphabet:
                        probs[i][alphabet.index(c_simp)] += probs[i][alphabet.index(c)]
                        probs[i][alphabet.index(c)] = 0

        return [rect, text, mean_confidence_score, indices, probs]


cnocr = None
def ocr_for_single_lines_probs_CnOCR(img, *args):
    global cnocr
    img_list = [img]

    if len(img_list) == 0:
        return []

    img_list = [cnocr._preprocess_img_array(img) for img in img_list]

    batch_size = len(img_list)
    img_list, img_widths = cnocr._pad_arrays(img_list)

    prob = cnocr._predict(mx.nd.array(img_list))
    # [seq_len, batch_size, num_classes]
    prob = np.reshape(prob, (-1, batch_size, prob.shape[1]))

    if cnocr._cand_alph_idx is not None:
        prob = prob * cnocr._gen_mask(prob.shape)

    max_width = max(img_widths)
    res = []
    probs = []
    prob_distributions = []
    for i in range(batch_size):
        line_prob = prob[:, i, :]
        class_ids = np.argmax(line_prob, axis=-1)
        chars, start_end_indices = gen_line_pred_chars(cnocr, line_prob, img_widths[i], max_width)
        batch_probs = []
        batch_prob_distributions = []
        for char, (start, end) in zip(chars, start_end_indices):
            idx_probs = line_prob[start:end].mean(axis=0)

            # Smooth out OCR distribution a bit, because it tends to be over confident
            idx_probs = np.sqrt(idx_probs)
            idx_probs = idx_probs / idx_probs.sum()

            batch_prob_distributions.append(idx_probs)
            batch_probs.append(idx_probs[cnocr._alphabet.index(char)])

        probs.append(batch_probs)
        prob_distributions.append(batch_prob_distributions)
        res.append(chars)

    return ''.join(res[0]), np.array(probs)[0], prob_distributions[0]


def gen_line_pred_chars(ocr, line_prob, img_width, max_img_width):
    """
    Get the predicted characters.
    :param line_prob: with shape of [seq_length, num_classes]
    :param img_width:
    :param max_img_width:
    :return:
    """
    class_ids = np.argmax(line_prob, axis=-1)

    if img_width < max_img_width:
        comp_ratio = ocr._hp.seq_len_cmpr_ratio
        end_idx = img_width // comp_ratio
        if end_idx < len(class_ids):
            class_ids[end_idx:] = 0
    prediction, start_end_idx = CtcMetrics.ctc_label(class_ids.tolist())
    alphabet = ocr._alphabet
    res = [alphabet[p] if alphabet[p] != '<space>' else ' ' for p in prediction]

    return res, start_end_idx


def ocr_for_single_lines_probs(ocr, alphabet, segmentation, img, smooth_distributions=False):
    margin = 0.1
    text_threshold = 0.7
    min_size = 20

    results = ocr.readtext(segmentation)#, add_margin=margin, min_size=min_size, text_threshold=text_threshold)
    result = _join_predictions(results, alphabet)
    if result[0] == None:
        # Wider margin, lower thresholds seems to be needed for single chars
        margin = 0.5
        text_threshold = 0.3
        min_size = 10
        results = ocr.readtext(segmentation)#, add_margin=margin, min_size=min_size, text_threshold=text_threshold)
        result = _join_predictions(results, alphabet)

    box, text, confidence, prob_indices, prob_distributions = result
    """
    if confidence < 0.6 and len(img) > 0:
        results = ocr.readtext(img)#, add_margin=margin, min_size=min_size, text_threshold=text_threshold)
        result = _join_predictions(results, alphabet)
        img_confidence = result[2]
        img_text = result[1]
        print(f"{img_confidence = } {confidence = } {img_text = } {text = }")
        #cv2.imshow("img", img)
        #cv2.waitKey()
        if img_confidence > confidence:
            box, text, confidence, prob_indices, prob_distributions = result
    """

    if smooth_distributions:
        # Smooth out OCR distribution a bit, because it tends to be over confident
        # NOTE: correction: this was true for CnOCR, but not for EasyOCR
        for i in range(len(text)):
            prob_distributions[i, :] = np.sqrt(prob_distributions[i, :])
            prob_distributions[i, :] = prob_distributions[i, :] / prob_distributions[i, :].sum()

    probs = np.array([prob_distributions[i][idx] for i, idx in enumerate(prob_indices)])
    return text, probs, prob_distributions


def srt_timestamp(t):
    hours = int(t // (60*60))
    t -= hours * 60 * 60
    minutes = int(t // 60)
    t -= minutes * 60
    seconds = t
    return f'{hours:02}:{minutes:02}:{seconds:.3f}'.replace('.', ',')


def predict_chars(ocr_fn, mask, probs, img, window_buffer=10):
    if mask.sum() == 0:
        return '', None, None
    ys, xs = np.where(mask > 0)
    x_max, x_min = xs.max()+1, xs.min()
    y_max, y_min = ys.max()+1, ys.min()
    probs_crop = probs[y_min:y_max, x_min:x_max]
    img_crop = img[y_min:y_max, x_min:x_max, :]

    probs_larger = np.zeros((probs_crop.shape[0]+2*window_buffer, probs_crop.shape[1]+2*window_buffer), 'uint8')
    probs_larger[window_buffer:-window_buffer, window_buffer:-window_buffer] = (255*probs_crop).astype('uint8')
    probs_larger = 255 - probs_larger

    img_crop_larger = np.zeros((img_crop.shape[0]+2*window_buffer, img_crop.shape[1]+2*window_buffer, 3), 'uint8')
    img_crop_larger[window_buffer:-window_buffer, window_buffer:-window_buffer, :] = img_crop

    res, line_prob, prob_distributions = ocr_fn(probs_larger, img_crop_larger)
    return res, line_prob, prob_distributions


def jeffrey_div(a, b, eps=0.00001):
    a = a + eps
    b = b + eps
    return np.sum((a-b) * (np.log(a) - np.log(b)))


def get_BERT_masked_prob_distribution(text, mask_idx_start, mask_idx_end, alphabet):
    global tokenizer, model
    if tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained("hfl/chinese-bert-wwm")
        model = AutoModelForMaskedLM.from_pretrained("hfl/chinese-bert-wwm")

    masked_text = text[:mask_idx_start] + '[MASK]' + text[mask_idx_end:]
    inputs = tokenizer.encode_plus(masked_text, return_tensors="pt")
    output = model(**inputs)

    logits = output.logits
    softmax = F.softmax(logits, dim = -1)
    mask_index = torch.where(inputs["input_ids"][0] == tokenizer.mask_token_id)
    mask_word = softmax[0, mask_index, :]

    # TODO: move this out and do it once
    # Translate from BERT vocab to OCR vocab
    ocr_bert_indices = []
    for ocr_v in alphabet[1:]:
        idx = tokenizer.encode(ocr_v)[1]
        ocr_bert_indices.append(idx)

    ocr_bert_indices = np.array(ocr_bert_indices)
    unk_tokens = ocr_bert_indices == tokenizer.encode('[UNK]')[1]
    probs = mask_word[0, ocr_bert_indices]
    probs[unk_tokens] = 0
    probs = np.concatenate((np.array([0]), probs.detach().numpy()))
    # Reduce over confidence
    probs = np.sqrt(probs)
    probs = probs / probs.sum()
    return probs


def apply_BERT_prior(line, alphabet, context='', multiply=True):
    if line.char_probs is None or line.prob_distributions is None:
        return

    # Check all the char probs for low prob characters, apply BERT masked probabilities as a kind of prior
    applied = []
    for char_i, (char_prob, prob_distribution) in enumerate(zip(line.char_probs, line.prob_distributions)):
        if char_prob >= 0.998:
            continue

        bert_distribution = get_BERT_masked_prob_distribution(
            context + line.text,
            len(context) + char_i,
            len(context) + char_i+1,
            alphabet
        )
        applied += [line.text[char_i]]

        if multiply:
            updated_distribution = prob_distribution * bert_distribution
            updated_distribution = updated_distribution / updated_distribution.sum()  # normalize

            def _print_char(char):
                print('prob_distribution:', char, prob_distribution[alphabet.index(char)])
                print('bert_distribution:', char, bert_distribution[alphabet.index(char)])
                print('updated_distribution:', char, updated_distribution[alphabet.index(char)])

            """
            char = '丽'
            if line.text[char_i] == char:
                _print_char(char)
                _print_char('两')
                breakpoint()
            """
        else:
            # Average
            updated_distribution = (prob_distribution * bert_distribution) / 2

        prev_max = np.argmax(prob_distribution)
        updated_max = np.argmax(updated_distribution)
        if prev_max != updated_max:
            old_char = alphabet[prev_max]
            new_char = alphabet[updated_max]
            if len(filter_text_hanzi(new_char)) == 0:
                return  # never change to a non-hanzi character

            old_char_trad = HanziConv.toTraditional(old_char)
            new_char_trad = HanziConv.toTraditional(new_char)
            if old_char_trad != old_char or new_char_trad != new_char:
                print(f'{old_char} ({old_char_trad}) --> {new_char} ({new_char_trad}):  {char_prob}')
            else:
                print(f'{old_char} --> {new_char}:  {char_prob}')
            line.text = line.text[:char_i] + new_char + line.text[char_i+1:]

        line.prob_distributions[char_i] = updated_distribution
        line.char_probs[char_i] = updated_distribution.max()

    if len(applied) > 0:
        print(f'Used BERT prior for {", ".join(applied)} / {line.text}')


def apply_english_corrections(line):
    pass


def get_video_length_size(path):
    size_bytes = os.path.getsize(path)
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        return 0, size_bytes
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    return round(frame_count/fps, 2), size_bytes, (height, width)


def find_sync_point(video_path):
    cap = cv2.VideoCapture(video_path)

    colors = [
        ('blue', np.array([255, 0, 0])),
        ('green', np.array([0, 255, 0])),
        ('red', np.array([0, 0, 255])),
    ]
    seen_red = False
    seen_green = False
    seen_blue = False
    done = False
    intersection = None
    height, width = None, None
    while cap.isOpened():
        ret, frame = cap.read()
        print('frame', i)

        if frame is None:
            break

        if width is None:
            height, width = frame.shape[:2]

        for name, color in colors:
            diff = np.linalg.norm(frame.astype('int') - color, axis=-1).astype('int')
            mask = diff < 25
            mask_large_components = filter_components(mask, small_threshold=100*100)
            if mask_large_components.sum() > 0:
                if not seen_red and name == 'red':
                    seen_red = True
                    print('seen red')
                    intersection = mask_large_components
                    cv2.imshow('intersection', 255*intersection.astype('uint8'))
                    key = cv2.waitKey()
                    break
                elif seen_red and not seen_green and name == 'green':
                    seen_green = True
                    print('seen green')
                    intersection = intersection & mask_large_components
                    cv2.imshow('intersection', 255*intersection.astype('uint8'))
                    key = cv2.waitKey()
                    break
                elif seen_red and seen_green and not seen_blue and name == 'blue':
                    seen_blue = True
                    print('seen blue')
                    intersection = intersection & mask_large_components
                    cv2.imshow('intersection', 255*intersection.astype('uint8'))
                    key = cv2.waitKey()
                    break
            elif seen_blue:
                # We're done
                done = True
                print('done')
                break

        if done:
            curr_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
            ys, xs = np.where(intersection)
            x_max, x_min = xs.max()+1, xs.min()
            y_max, y_min = ys.max()+1, ys.min()
            if DEBUG:
                cv2.imshow('intersection', 255*intersection.astype('uint8'))
                key = cv2.waitKey()
            cap.release()
            return curr_time, y_min, x_min, y_max, x_max, height, width

        if DEBUG:
            cv2.imshow('frame', frame)
            cv2.waitKey()

    cap.release()


def get_video_caption_area(
    video_path: str,
    caption_top: float,
    caption_bottom: float,
    caption_left: float=0.0,
    caption_right: float=1.0,
    start_time_s: float=0,
    end_time_s: float=None,
    out_height=80,
    font_height=60,
    height_buffer_px=0,
):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, start_time_s*1000)

    if end_time_s is not None and end_time_s < 0:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        video_length = frame_count / fps
        end_time_s = video_length + end_time_s

    last_delta = 0
    last_time = 0
    while cap.isOpened():
        ret, frame = cap.read()

        if frame is None:
            break

        if DEBUG:
            cv2.imshow('frame', frame)
            key = cv2.waitKey()

        caption_top_px = int(caption_top * frame.shape[0])
        caption_bottom_px = int(caption_bottom * frame.shape[0])
        caption_left_px = int(caption_left * frame.shape[1])
        caption_right_px = int(caption_right * frame.shape[1])

        # First scale it to the right resolution
        scale_factor = font_height / (caption_bottom_px - caption_top_px)
        resized = cv2.resize(frame, (int(frame.shape[1] * scale_factor), int(frame.shape[0] * scale_factor)), interpolation=cv2.INTER_LANCZOS4)
        top_resized = int(caption_top_px * scale_factor)
        bottom_resized = int(caption_bottom_px * scale_factor)
        left_resized = int(caption_left_px * scale_factor)
        right_resized = int(caption_right_px * scale_factor)

        padding = (out_height - font_height) // 2

        top = top_resized-padding-height_buffer_px
        bottom = top + out_height + 2*height_buffer_px
        crop = resized[top:bottom, left_resized:right_resized]
        if crop.shape[0] != out_height + 2*height_buffer_px:
            breakpoint()
        assert crop.shape[0] == out_height + 2*height_buffer_px

        curr_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        if curr_time > 0 and last_time > 0:
            last_delta = curr_time - last_time

        # NOTE: OK, weirdest thing I had to debug: the above call returns 0.0 every 12th frame, which fucks up all manner of things
        # so interpolate the time using the last frame delta we saw
        if curr_time == 0 and last_delta != 0:
            curr_time = last_time + last_delta / 2

        last_time = curr_time
        yield curr_time, crop, frame

        if end_time_s is not None and curr_time >= end_time_s:
            break

    cap.release()
    if DEBUG:
        cv2.destroyAllWindows()


def mean_frame_diff(img1, img2, mask=None):
    if mask is None:
        return np.abs(img1.astype('float') - img2.astype('float')).mean()

    if mask.sum() == 0:
        return 0
    return np.abs(img1[mask].astype('float') - img2[mask].astype('float')).mean()


def filter_components(mask, small_threshold=25):
    contours, hierarchy = cv2.findContours(255*mask.astype('uint8'), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    new_mask = np.zeros_like(mask, dtype='uint8')
    for i, contour in enumerate(contours):
        if cv2.contourArea(contour) < small_threshold:
            continue

        cv2.drawContours(new_mask, contours, i, 255, -1, hierarchy=hierarchy)

    return new_mask > 0


def frames_diff(frame, last_frame, dominant_caption_color, height_buffer_px):
    if dominant_caption_color is None:
        return mean_frame_diff(frame, last_frame) < 1.0

    color_distance_threshold = 30
    frame = cv2.blur(frame, (3, 3))
    last_frame = cv2.blur(last_frame, (3, 3))

    frame_dominant_color = np.linalg.norm(np.abs(frame.astype(float) - dominant_caption_color), axis=2) < color_distance_threshold
    last_frame_dominant_color = np.linalg.norm(np.abs(last_frame.astype(float) - dominant_caption_color), axis=2) < color_distance_threshold
    intersection = (frame_dominant_color & last_frame_dominant_color).sum()
    union = (frame_dominant_color | last_frame_dominant_color).sum()
    intersection_over_union = intersection / union if union > 0 else 1

    #print(dominant_caption_color)
    #print(intersection_over_union)
    #cv2.imshow('frame', frame)
    #cv2.imshow('last_frame', last_frame)
    #cv2.imshow('frame_dominant_color', (255*frame_dominant_color).astype('uint8'))
    #cv2.imshow('last_frame_dominant_color', (255*last_frame_dominant_color).astype('uint8'))
    #cv2.waitKey()
    return intersection_over_union < 0.97


def find_next_diff(line, buffer_frames, threshold=10, height_buffer_px=0):
    # Go back through the frame buffer to determine the change if any
    frame_blur = cv2.blur(line.img, (3,3))

    for i, (buffer_t, buffer_frame) in enumerate(buffer_frames):
        if height_buffer_px > 0:
            buffer_frame = buffer_frame[height_buffer_px:-height_buffer_px, ...]
        buffer_frame_blur = cv2.blur(buffer_frame, (3,3))
        mean_diff = mean_frame_diff(buffer_frame_blur, frame_blur, line.mask)
        if mean_diff > threshold:
            return i

    return None


net = _get_latest_net()

def predict_line(ocr_fn, frame, frame_t, font_height, conditional_caption_idx=None, height_buffer_px=0):
    mask, probs = predict_img_pipeline(frame, net)
    mask.cache = None
    probs.cache = None
    mask = mask.eval()
    probs = probs.eval()
    text, char_probs, prob_distributions = predict_chars(ocr_fn, mask, probs, frame)

    # Remove the height buffer that was added when extracting the frames from the video
    if height_buffer_px > 0:
        frame = frame[height_buffer_px:-height_buffer_px, ...]
        mask = mask[height_buffer_px:-height_buffer_px, ...]
        probs = probs[height_buffer_px:-height_buffer_px, ...]

    logprob = None
    if char_probs is not None:
        logprob = np.sum(np.log(char_probs))

    mask = mask > 0
    bounding_rect = None
    frame_copy = frame.copy()
    if mask.sum() > 0:
        mask_large_components = filter_components(mask, small_threshold=5*5)
        contours, _ = cv2.findContours(255*mask_large_components.astype('uint8'), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        min_x, min_y = frame.shape[1], frame.shape[0]
        max_x = max_y = 0

        for contour in contours:
            (x,y,w,h) = cv2.boundingRect(contour)
            min_x, max_x = min(x, min_x), max(x+w, max_x)
            min_y, max_y = min(y, min_y), max(y+h, max_y)

        cv2.rectangle(frame_copy, (min_x, min_y),(max_x, max_y), (0, 255, 0), 3)

        bounding_rect = (min_x, max_x, min_y, max_y)

        desired_ratio = font_height / frame.shape[0]
        actual_ratio = (max_y - min_y) / frame.shape[0]
        print('actual_ratio', actual_ratio)
        if len(contours) == 0 or abs(actual_ratio - desired_ratio) > 0.15:
            print(f'{actual_ratio = } {desired_ratio = }')
            text = ''
            char_probs = None
            prob_distributions = None
            logprob = None


    cv2.imshow('frame', frame_copy)
    cv2.imshow('probs', (255*probs).astype('uint8'))
    cv2.waitKey(1)
    caption_line = CaptionLine(
        text, frame_t, frame_t, logprob,
        frame, mask > 0, probs,
        char_probs, prob_distributions,
        bounding_rect,
        conditional_caption_idx=conditional_caption_idx
    )
    return caption_line


def save_caption_data(video_id, caption_line, alphabet):
    h = hashlib.md5()
    h.update(bytes(video_id, 'utf-8'))
    h.update(bytes(caption_line.text, 'utf-8'))
    h.update(bytes(str(caption_line.t0), 'utf-8'))
    h.update(bytes(str(caption_line.t1), 'utf-8'))
    if caption_line.bounding_rect is not None:
        for x in caption_line.bounding_rect:
            h.update(bytes(str(x), 'utf-8'))

    data_hash = h.hexdigest()
    caption_line.data_hash = data_hash

    os.makedirs('data/remote/private/caption_data/images', exist_ok=True)
    os.makedirs('data/remote/private/caption_data/segmentation_probs', exist_ok=True)
    os.makedirs('data/remote/private/caption_data/char_probability_distributions', exist_ok=True)

    img_path = f'data/remote/private/caption_data/images/{data_hash}.jpg'
    caption_probs_path = f'data/remote/private/caption_data/segmentation_probs/{data_hash}.png'
    prob_distributions_path = f'data/remote/private/caption_data/char_probability_distributions/{data_hash}.pickle'
    if caption_line.img is not None and len(caption_line.img) > 0:
        cv2.imwrite(img_path, caption_line.img, [cv2.IMWRITE_JPEG_QUALITY, 90])


    if caption_line.text != '':
        cv2.imwrite(caption_probs_path, (caption_line.probs * 255).astype('uint8'))

        top10_char_probs = []
        for prob_distribution in caption_line.prob_distributions:
            top10_indices = np.argpartition(prob_distribution, -10)[-10:]
            top10_probs = [float(p) for p in prob_distribution[top10_indices]]
            top10_chars = [alphabet[idx] for idx in top10_indices]
            top10_char_probs.append(list(sorted(zip(top10_chars, top10_probs), key=lambda x: x[1], reverse=True)))

        with open(prob_distributions_path, 'wb') as f:
            pickle.dump(top10_char_probs, f)


def replace_or_add_line(
    video_id,
    new_line,
    caption_lines,
    alphabet,
    replace_levenshtein_threshold=1.0,
    zero_out_numpy=True,
    do_save_caption_data=True,
    filter_out_too_many_low_prob_chars=True,
    caption_type='hanzi',
    use_bert_prior=True,
    force_add=False,
):
    last_line = caption_lines[-1] if len(caption_lines) > 0 else None
    replaced = False

    if new_line.text != '' and not force_add:
        too_many_low_prob_chars = (new_line.char_probs < HIGH_PROB_CHAR).sum() / len(new_line.text) > 0.7 and len(new_line.text) > 1
        if (caption_type == 'hanzi' and len(filter_text_hanzi(new_line.text)) == 0) or (filter_out_too_many_low_prob_chars and too_many_low_prob_chars):
            print('Too many low prob characters:', new_line, ', removing')
            return last_line

    if last_line is not None and last_line.text != '' and new_line.text != '' and not force_add:
        def _subst_cost(s1, s2, i, j):
            if i >= len(last_line.prob_distributions) or j >= len(new_line.prob_distributions):
                # This happened when ocr output "[blank]". Keep this just in case. 
                # Edit: should be fixed now
                print('WARNING: out of bounds')
                return 1.0

            if s1 == ' ':
                # We have a very low penalty for substituting a space, since there are often spurious spaces in the OCR
                return 0.01

            return jeffrey_div(new_line.prob_distributions[j], last_line.prob_distributions[i])

        dist, ops = weighted_levenshtein(last_line.text, new_line.text, _subst_cost, return_ops=True)
        mean_dist = dist / min(len(new_line.text), len(last_line.text))
        if mean_dist < replace_levenshtein_threshold or last_line.text == new_line.text:
            # We think this line is not new, just noise on the previous line, so
            #  * pick the highest prob characters between the two when replaced
            #  * if a low probability character is inserted or deleted, we delete them

            new_text = ''
            new_char_probs = []
            new_prob_distributions = []
            inserted = 0
            for op in ops:
                if op.type == OpType.SUBSTITUTE:
                    # Update the char_probs and prob_distribution
                    #prob_distribution = last_line.prob_distributions[op.from_idx] * new_line.prob_distributions[op.to_idx]
                    #prob_distribution /= prob_distribution.sum()
                    prob_distribution = (last_line.prob_distributions[op.from_idx] + new_line.prob_distributions[op.to_idx]) / 2
                    char_prob = prob_distribution.max()
                    new_char = alphabet[np.argmax(prob_distribution)]
                    if new_char is not None and new_char != '[blank]':
                        new_text += new_char
                        new_char_probs.append(char_prob)
                        new_prob_distributions.append(prob_distribution)
                    inserted = 0
                elif op.type == OpType.DELETE:
                    if last_line.char_probs[op.from_idx] >= HIGH_PROB_CHAR and inserted == 0:
                        # Supposed to delete it, but since it's high probability we keep it anyway
                        new_text += last_line.text[op.from_idx]
                        new_char_probs.append(last_line.char_probs[op.from_idx])
                        new_prob_distributions.append(last_line.prob_distributions[op.from_idx])
                    else:
                        inserted -= 1
                elif op.type == OpType.INSERT:
                    if new_line.char_probs[op.to_idx] >= HIGH_PROB_CHAR:
                        new_text += new_line.text[op.to_idx]
                        new_char_probs.append(new_line.char_probs[op.to_idx])
                        new_prob_distributions.append(new_line.prob_distributions[op.to_idx])
                        inserted +=1

            new_char_probs = np.array(new_char_probs)
            new_logprob = np.sum(np.log(new_char_probs))
            if new_prob_distributions is None:
                breakpoint()
            new_line = CaptionLine(
                new_text, last_line.t0, new_line.t1, new_logprob,
                new_line.img, new_line.mask, new_line.probs,
                new_char_probs, new_prob_distributions,
                new_line.bounding_rect,
                conditional_caption_idx=new_line.conditional_caption_idx
            )
            caption_lines[-1] = new_line
            print('Replacing', new_line)
            replaced = True
        else:
            new_line.t0 = last_line.t1

        new_line.mean_dist = mean_dist

    if not replaced:
        # Now that we have definitely moved on to a new line, we apply the BERT prior to the previous one,
        if len(caption_lines) > 0:
            last_line = caption_lines[-1]
            if caption_type == 'hanzi' and use_bert_prior:
                apply_BERT_prior(last_line, alphabet)
            #elif caption_type == 'english':
                #apply_english_corrections(last_line)
            #elif caption_type == 'pinyin':
                #raise NotImplemented

    last_line = caption_lines[-1] if len(caption_lines) > 0 else None
    if last_line is not None:
        if last_line.text == '' and new_line.text == '':
            last_line.t1 = new_line.t1
            print(f'Updated last_line.t1 {last_line}')
            return last_line  # return here so we don't add
        elif last_line.text == '':
            new_line.t0 = last_line.t1
            print(f'Updated new_line.t0 {new_line}')
        elif new_line.text == '':
            last_line.t1 = new_line.t0
            print(f'Updated last_line.t1 {last_line}')

    if not replaced:
        if len(caption_lines) > 0:
            # Need to save the caption data before zeroing out
            if do_save_caption_data:
                print(f'Saving {len(caption_lines)}')
                save_caption_data(video_id, caption_lines[-1], alphabet)

            if zero_out_numpy:
                print(f'Zeroing out {len(caption_lines)}')
                caption_lines[-1].zero_out_numpy()

        print(f'Adding {new_line}')
        caption_lines.append(new_line)

    return new_line


def extract_lines_from_framebuffer(ocr_fn, last_line, frame_buffer, font_height, line=None, frame_t=None, threshold=10, height_buffer_px=0):
    if len(frame_buffer) == 0:
        return []

    if line is None:
        frame_t, frame = frame_buffer.pop(-1)
        line = predict_line(ocr_fn, frame, frame_t, font_height, height_buffer_px=height_buffer_px)

    if line.text == '':
        if last_line is None:
            print(f'None -> E ({frame_t})')
            return [line]  # If there is anything in between, we can't find it without any masks
        elif last_line.text == '':
            print(f'E -> E ({frame_t})')
            return [line]

        # Go forwards from last_line
        diff_idx = find_next_diff(last_line, frame_buffer, threshold=threshold, height_buffer_px=height_buffer_px)
        if diff_idx is None:
            print(f'{last_line} --> no diff ({frame_t})')
            return [line]  # didn't find any diff

        diff_t, diff_frame = frame_buffer[diff_idx]
        diff_line = predict_line(ocr_fn, diff_frame, diff_t, font_height, height_buffer_px=height_buffer_px)
        print(f'last_line: {last_line} --> diff_line: {diff_line} --> ? --> E ({frame_t})')
        return [diff_line] + extract_lines_from_framebuffer(ocr_fn, diff_line, frame_buffer[diff_idx:], font_height, line, frame_t, threshold=threshold, height_buffer_px=height_buffer_px) + [line]
    else:
        # Go backwards from line
        diff_idx = find_next_diff(line, reversed(frame_buffer), threshold=threshold, height_buffer_px=height_buffer_px)

        if diff_idx is None:
            print(f'no diff <- O ({frame_t})')
            return [line] # no diff

        print(f'last_line {last_line} <-- ? <-- {line} ({frame_t})')
        frames_left = list(reversed(list(reversed(frame_buffer))[diff_idx:]))
        return extract_lines_from_framebuffer(ocr_fn, last_line, frames_left, font_height, threshold=threshold, height_buffer_px=height_buffer_px) + [line]


@task(deps=[net])
def extract_video_captions(
    video_path: str,
    video_id: str,
    caption_top: float,
    caption_bottom: float,
    caption_left: float=0.0,
    caption_right: float=1.0,
    start_time_s: float=0,
    end_time_s: float=None,
    out_height=80,
    font_height=60,
    height_buffer_px=0,
    replace_levenshtein_threshold=1.0,
    filter_out_too_many_low_prob_chars=True,
    zero_out_numpy=True,
    do_save_caption_data=True,
    caption_type='hanzi',
    ocr_engine='cnocr',
    use_bert_prior=True,
    conditional_captions=None,
    refine_bounding_rect=False,
    screen_recording_video_timings=None,
):
    global easy_ocrs, cnocr
    SUBSAMPLE_SECONDS = 1/3
    print('Processing video', video_path)

    lang = None
    if caption_type == 'hanzi':
        lang = ['ch_sim', 'en']
    elif caption_type == 'english':
        lang = ['en']
    elif caption_type == 'pinyin':
        raise NotImplemented()

    if ocr_engine == 'easyocr':
        if easy_ocrs is None:
            easy_ocrs = {
                'en': Reader(['en']),
                'ch_sim,en': Reader(['ch_sim', 'en']),
            }

        ocr = easy_ocrs[','.join(sorted(lang))]
        alphabet = ocr.converter.character
        ocr_fn = partial(ocr_for_single_lines_probs, ocr, alphabet)
    else:
        if cnocr is None:
            cnocr = CnOcr()
        ocr_fn = ocr_for_single_lines_probs_CnOCR
        alphabet = cnocr._alphabet

    if screen_recording_video_timings is not None:
        print('Screen recording video timings provided, trying to find sync point')
        sync_time, sync_top, sync_left, sync_bottom, sync_right, sync_height, sync_width = find_sync_point(video_path)
        caption_top = sync_top / sync_height
        caption_left = sync_left / sync_width
        caption_bottom = sync_bottom / sync_height
        caption_right = sync_right / sync_width

    # Find the text bounding rects of a bunch of frames and adjust caption_top/bottom
    frame_size = None
    iters = 1 if refine_bounding_rect else 0
    subsample_frames_until_first_seen = 30*15 # 25 seconds
    subsample_frames_after_first_seen = 30*2 # 2 seconds
    for j in range(iters):
        best_top_bottom = None
        best_logprob_sum = -float('inf')
        best_offset = 0
        offsets = [0] if j >= 1 else range(-2, 3)
        for y_offset in offsets:
            y_offset /= 500
            caption_images = get_video_caption_area(
                video_path, caption_top+y_offset, caption_bottom+y_offset, caption_left, caption_right, start_time_s, end_time_s, out_height, font_height, height_buffer_px
            )
            num_added = 0
            sum_log_prob = 0
            bounding_rects = []
            for i, (frame_time, crop, frame) in enumerate(caption_images):
                if len(bounding_rects) == 0 and i % subsample_frames_until_first_seen != 0:
                    print('Skipping not seen first yet')
                    continue

                if len(bounding_rects) > 0 and i % subsample_frames_after_first_seen != 0:
                    print('Skipping has seen first')
                    continue

                if frame_size is None:
                    frame_size = frame.shape[:2]

                line = predict_line(ocr_fn, crop, frame_time, font_height, height_buffer_px=height_buffer_px)
                print(line.text)
                if (len(filter_text_hanzi(line.text)) > 1 or len(line.text) > 5) and line.bounding_rect is not None:
                    sum_log_prob += line.logprob
                    bounding_rects.append(line.bounding_rect)

                line.zero_out_numpy()

                if len(bounding_rects) > 10 or (len(bounding_rects) > 0 and frame_time - start_time_s > 120):
                    break

            if sum_log_prob > best_logprob_sum and len(bounding_rects) > 0:
                best_logprob_sum = sum_log_prob
                best_offset = y_offset
                mean_crop_caption_top = np.array([min_y for (_, _, min_y, _) in bounding_rects]).mean()
                mean_crop_caption_bottom = np.array([max_y for (_, _, _, max_y) in bounding_rects]).mean()
                best_top_bottom = [mean_crop_caption_top, mean_crop_caption_bottom]

        caption_top_px = int(caption_top * frame.shape[0])
        caption_bottom_px = int(caption_bottom * frame.shape[0])
        crop_scale = (caption_bottom_px - caption_top_px) / font_height
        expected_crop_caption_top = (out_height - font_height) / 2
        expected_crop_caption_bottom = out_height - expected_crop_caption_top

        caption_top += best_offset
        caption_bottom += best_offset
        top_diff_px = (best_top_bottom[0] - expected_crop_caption_top) * crop_scale
        bottom_diff_px = (best_top_bottom[1] - expected_crop_caption_bottom) * crop_scale
        caption_top += top_diff_px / frame_size[0]
        caption_bottom += bottom_diff_px / frame_size[0]

    caption_images = get_video_caption_area(
        video_path, caption_top, caption_bottom, caption_left, caption_right, start_time_s, end_time_s, out_height, font_height, height_buffer_px
    )

    frame_buffer = []
    caption_lines = []
    dominant_caption_color = None
    last_processed_frame = None
    curr_conditional_caption_idx = 0
    try:
        for i, (frame_time, crop, frame) in enumerate(caption_images):
            if frame_size is None:
                frame_size = frame.shape[:2]

            if conditional_captions is not None:
                if curr_conditional_caption_idx is None:
                    continue

                cond_start = conditional_captions['lines'][curr_conditional_caption_idx][1]
                cond_end = conditional_captions['lines'][curr_conditional_caption_idx][2]
                if frame_time < cond_start:
                    continue
                if frame_time > cond_end:
                    if len(frame_buffer) == 0:
                        # The conditional time range was too short, there were no frames
                        frame_t = (cond_end + cond_start) / 2
                        line = CaptionLine('', cond_start, cond_end, 0, None, None, None, None, None)
                    else:
                        frame_t, frame = frame_buffer[len(frame_buffer) // 2]
                        line = predict_line(ocr_fn, frame, frame_t, font_height, curr_conditional_caption_idx, height_buffer_px=height_buffer_px)

                    frame_buffer_lines = [line]

                    curr_conditional_caption_idx += 1
                    if curr_conditional_caption_idx >= len(conditional_captions['lines']):
                        curr_conditional_caption_idx = None
                else:
                    if frame_time[-1][0] - frame_time[0][0] < 1:
                        frame_buffer.append((frame_time, crop))
                    continue
            else:
                frame_buffer.append((frame_time, crop))

                if i != 0 and frame_buffer[-1][0] - frame_buffer[0][0] < SUBSAMPLE_SECONDS:
                    print('buffering')
                    continue

                check_diff_against_frame = last_processed_frame if last_processed_frame is not None else frame_buffer[0][1]
                if i != 0 and not frames_diff(crop, check_diff_against_frame, dominant_caption_color, height_buffer_px) and len(frame_buffer) < 40:
                    print('no diff')
                    continue

                print('diff')

                last_line = caption_lines[-1] if len(caption_lines) > 0 else None
                frame_buffer_lines = extract_lines_from_framebuffer(ocr_fn, last_line, frame_buffer, font_height, height_buffer_px=height_buffer_px)

            for line in frame_buffer_lines:
                if line.text != '':
                    dominant_caption_color = np.median(line.img[line.mask], axis=0)

                caption_top_px = int(caption_top * frame_size[0])
                caption_bottom_px = int(caption_bottom * frame_size[0])
                caption_left_px = int(caption_left * frame_size[1])

                if line.bounding_rect:
                    # Transform bounding rect from local coordinates (in the scaled cropped image fed to OCR), to global
                    padding = (out_height - font_height) // 2
                    scale_factor = font_height / (caption_bottom_px - caption_top_px)
                    min_x, max_x, min_y, max_y = line.bounding_rect
                    min_y -= padding
                    max_y -= padding

                    line.bounding_rect = (
                        int(min_x / scale_factor) + caption_left_px,
                        int(max_x / scale_factor) + caption_left_px,
                        int(min_y / scale_factor) + caption_top_px, # Add caption top to get global coordinates
                        int(max_y / scale_factor) + caption_top_px
                    )

                    #frame_copy = frame.copy()
                    #(x_min, x_max, y_min, y_max) = line.bounding_rect
                    #cv2.rectangle(frame_copy, (x_min, caption_top+y_min), (x_max, caption_top+y_max), (0, 255, 0), 3)
                    #cv2.imshow('full frame', frame_copy)
                    #cv2.waitKey()

                #if (line.t0 == 0 or line.t1 == 0) and line.text != '':
                    #breakpoint()
                line = replace_or_add_line(
                    video_id,
                    line,
                    caption_lines,
                    alphabet,
                    replace_levenshtein_threshold,
                    zero_out_numpy,
                    do_save_caption_data,
                    filter_out_too_many_low_prob_chars,
                    caption_type,
                    use_bert_prior=use_bert_prior,
                    force_add=conditional_captions is not None,
                )
                #if (line.t0 == 0 or line.t1 == 0) and line.text != '':
                    #breakpoint()

            last_processed_frame = frame_buffer[-1][1] if len(frame_buffer) > 0 else None
            frame_buffer.clear()
    except KeyboardInterrupt:
        # If we get Ctrl-C we stop the processing, assuming that the rest is credits
        response = input('Would you like to save the result so far? Y/n: ')
        if response != 'Y':
            raise

    # Need to save the last caption (the rest are saved in `replace_or_add_line` before zeroing out)
    if caption_lines[-1].text != '' and do_save_caption_data:
        save_caption_data(video_id, caption_lines[-1], alphabet)

    return caption_lines, frame_size


@task(serializer=json)
def update_conditional_captions(caption_lines, conditional_captions, action):
    assert 'type' in action
    assert ('join' in action) or action['type'] == 'assign'

    # We update the original conditional captions and return those instead
    for cond_line in conditional_captions['lines']:
        cond_line_t0, cond_line_t1 = cond_line[1], cond_line[2]
        if cond_line[3] is None:
            continue

        for i in range(len(caption_lines['lines'])):
            line = caption_lines['lines'][i]
            line_t0, line_t1 = line[1], line[2]
            if line[3] is None:
                continue

            if line_t0 > cond_line_t1 or line_t1 < cond_line_t0:
                # No overlap
                continue

            # Prepend the text
            if action['type'] == 'prepend':
                if line[0].strip() != '':
                    cond_line[0] = line[0] + action['join'] + cond_line[0]
            elif action['type'] == 'append':
                if cond_line[0].strip() == '':
                    cond_line[0] = line[0]
                else:
                    cond_line[0] = cond_line[0] + action['join'] + line[0]
            elif action['type'] == 'replace':
                cond_line[0] = line[0]

            # Take the bounding rect union
            cond_rect = list(cond_line[3])
            if line[3] is not None and len(line[3]) == 4:
                cond_rect[0] = min(cond_rect[0], line[3][0])  # min x
                cond_rect[1] = max(cond_rect[1], line[3][1])  # max x
                cond_rect[2] = min(cond_rect[2], line[3][2])  # min y
                cond_rect[3] = max(cond_rect[3], line[3][3])  # max y
            cond_line[3] = cond_rect
            break

    return conditional_captions


@task(serializer=json, outs=1)
def caption_lines_to_json(lines, frame_size, params, video_length, conditional_params=None):
    json_lines = []

    for line in lines:
        char_probs = [float(prob) for prob in line.char_probs] if line.char_probs is not None else None
        json_lines.append([
            line.text,
            line.t0,
            line.t1,
            line.bounding_rect,
            char_probs,
            float(line.logprob) if line.logprob is not None else None,
            line.data_hash
        ])
        print(line.text)

    caption_top = params['caption_top']
    if conditional_params is not None:
        caption_top = min(caption_top, conditional_params['caption_top'])

    return {
        'video_length': video_length,
        'lines': json_lines,
        'frame_size': frame_size,
        'caption_top': caption_top,
    }


@task
def compare_video_captions_to_truth(captions, true_srt):
    srt_captions = []
    with open(true_srt, 'r') as f:
        srt_json = json.loads(f.read())
        for event in srt_json['events']:
            srt_captions.append((
                event['segs'][0]['utf8'],
                event['tStartMs']/1000,
                (event['tStartMs'] + event['dDurationMs'])/1000)
            )

    errors = 0
    total_chars = 0
    last_matched_srt_line = -1
    matched_srt_lines = []
    for line in captions:
        ocr_start, ocr_end = line.t0, line.t1
        matched = False
        for i in range(last_matched_srt_line + 1, len(srt_captions)):
            srt_line = srt_captions[i]
            srt_start, srt_end = srt_line[1:3]
            intersection_start = max(ocr_start, srt_start)
            intersection_end = min(ocr_end, srt_end)
            if intersection_end < intersection_start:
                continue

            dist = weighted_levenshtein(filter_text_hanzi(line.text), filter_text_hanzi(srt_line[0]))

            if (
                (intersection_end - intersection_start) / max(0.1, (ocr_end - ocr_start)) < 0.5 and
                (intersection_end - intersection_start) / (srt_end - srt_start) < 0.5
            ):
                if dist / len(filter_text_hanzi(line.text)) < 0.1:

                    print('Intersection too small, skipping, but similar', line, srt_line)
                else:
                    continue

            if dist > 0:
                print(line, srt_line, dist)
                #cv2.imshow("img", line.img)
                #cv2.imshow("mask", line.mask)
                #cv2.imshow("probs", line.probs)
                #cv2.waitKey()

            errors += dist
            total_chars += len(filter_text_hanzi(line.text))
            last_matched_srt_line = i
            matched_srt_lines.append(i)
            matched = True
            print('Matched', line.text)
            break

        if not matched:
            print('Couldnt match', line)

    matched_srt_lines = set(matched_srt_lines)
    for i, caption in enumerate(srt_captions):
        if i not in matched_srt_lines:
            print(f'Srt line not matched: {caption}')
            errors += len(caption[0])
            total_chars += len(caption[0])

    return errors, total_chars


def timestamp_to_seconds(timestamp):
    parts = [float(part) for part in timestamp.split(':')]
    return parts[0] * 60 * 60 + parts[1] * 60 + parts[2]


def convert_vtt_to_caption_format(translations_path, params=None, video_length=None, frame_size=None):
    translations = [t for t in webvtt.read(translations_path)]
    # Convert newlines to spaces
    lines = []
    for i, caption in enumerate(translations):
        text = caption.text.replace('\n', ' ')
        t0 = timestamp_to_seconds(caption.start)
        t1 = timestamp_to_seconds(caption.end)
        if i > 0:
            # Fix overlapping captions
            last_t1 = timestamp_to_seconds(translations[i-1].end)
            if last_t1 > t0:
                lines[i-1][2] = t0

        lines.append([text, t0, t1, None, None, None, None])

    data = {
        'lines': lines
    }
    if params is not None:
        if 'caption_top' in params[0]:
            data['caption_top'] = params[0]['caption_top']
        if 'caption_bottom' in params[0]:
            data['caption_bottom'] = params[0]['caption_bottom']
        if 'caption_left' in params[0]:
            data['caption_left'] = params[0]['caption_left']
        if 'caption_right' in params[0]:
            data['caption_right'] = params[0]['caption_right']

    if video_length is not None:
        data['video_length'] = video_length;
    if frame_size is not None:
        data['frame_size'] = frame_size;

    return data


@task(serializer=json)
def add_human_translations_merge_lines(caption_data, ocr_params, human_translations=None, remove_unmatched_captions=True):
    caption_lines = caption_data['lines']
    make_caption_lines_lists(caption_lines)

    english_params = {}
    hanzi_params = {}
    for params in ocr_params:
        if params['type'] == 'hanzi':
            hanzi_params = params
        elif params['type'] == 'english':
            english_params = params

    english_offset = english_params.get('offset_time', 0.0)
    hanzi_offset = hanzi_params.get('offset_time', 0.0)
    caption_data['timing_offset'] = hanzi_offset

    if human_translations is not None:
        human_translations['timing_offset'] = english_offset
        human_translations_per_caption = len(human_translations['lines']) / len(caption_data['lines'])
        if human_translations_per_caption < 0.5 and remove_unmatched_captions:
            print(f'Too few human translations ({human_translations_per_caption} per caption, skipping')
            for line in caption_lines:
                line.append([])
            return caption_data

        align_translations_and_captions(
            caption_data,
            human_translations,
            remove_unmatched_captions=remove_unmatched_captions
        )  # updates captions
    else:
        # If there are no human translations, append empty list
        for line in caption_lines:
            line.append([])

    return caption_data


@task(serializer=json)
def add_machine_translations(caption_data, machine_translations):
    assert(len(machine_translations) == len(caption_data['lines']))
    for line, caption_line in zip(machine_translations, caption_data['lines']):
        caption_line[-1].append(line)

    return caption_data


@task(serializer=json)
def trim_bad_captions(caption_data):
    # Tried using the log prob, but is not very reliable. Works best to check for '-' and '=' and others which are very indicative
    # of garbage captions
    suspicious_chars = ['-', '～', '一', '二', '_', '灬', '…', '`', '/', '”', '丿']
    lines = caption_data['lines']
    keep = [True] * len(lines)
    first_suspicious = None
    for i, line in enumerate(lines):
        text = line[0]
        if text == '':
            keep[i] = False
            continue

        suspicious_count = sum(text.count(char) for char in suspicious_chars)

        if suspicious_count > 1 and suspicious_count / len(text) > 0.6:
            if first_suspicious is None:
                first_suspicious = i
        else:
            if first_suspicious is not None and i - first_suspicious >= 2:
                for j in range(first_suspicious, i):
                    keep[j] = False
                    print(f'Trimming log logprob line {lines[j]}')
            first_suspicious = None

    new_lines = []
    for i, line in enumerate(caption_data['lines']):
        if keep[i]:
            new_lines.append(line)

    caption_data['lines'] = new_lines
    return caption_data


@task(serializer=json)
def add_metadata(caption_data, caption_id, show_name):
    caption_data['caption_id'] = caption_id
    caption_data['show_name'] = show_name
    caption_data['version'] = 1
    return caption_data


@task
def fix_fade(captions):
    # When there is fade in/out there is often an extra caption line at the
    # beginning/end. We can add an extra pass that identifies lines that are
    # similar enough, where the beginning/end are very quick. Then we pick the
    # longest duration one, since it's likely outside of the fade duration. 

    last_line = None
    new_lines = []
    for line in captions:
        if last_line is None or line.t0 - last_line.t1 > 0.03 or line.text == '' or last_line.text == '':
            # Not back-to-back
            last_line = line
            new_lines.append(line)
            print('1. Appending line', line)
            continue

        with open(f'data/remote/private/caption_data/char_probability_distributions/{last_line.data_hash}.pickle', 'rb') as f:
            last_line_prob_distributions = pickle.load(f)

        with open(f'data/remote/private/caption_data/char_probability_distributions/{line.data_hash}.pickle', 'rb') as f:
            line_prob_distributions = pickle.load(f)

        last_line_prob_chars = [set([c for c, _ in last_line_prob_distributions[i]]) for i in range(len(last_line_prob_distributions))]
        line_prob_chars = [set([c for c, _ in line_prob_distributions[i]]) for i in range(len(line_prob_distributions))]

        def _subst_cost(s1, s2, i, j):
            if s1 == ' ':
                # We have a very low penalty for substituting a space, since there are often spurious spaces in the OCR
                return 0.01

            if s1 in line_prob_chars[j] or s2 in last_line_prob_chars[i]:
                return 0

            if len(filter_text_hanzi(s1)) == 0 or len(filter_text_hanzi(s2)) == 0:
                return 0

            return 0 if s1 == s2 else 1

        dist, ops = weighted_levenshtein(last_line.text, line.text, _subst_cost, return_ops=True)
        mean_dist = dist / max(len(line.text), len(last_line.text))
        if (mean_dist <= 0.5 or last_line.text == line.text) and (line.t1-line.t0 < 0.1 or last_line.t1-last_line.t0 < 0.1):
            longest_line = line if line.t1 - line.t0 > last_line.t1 - last_line.t0 else last_line
            line = CaptionLine(
                longest_line.text, last_line.t0, line.t1, longest_line.logprob,
                longest_line.img, longest_line.mask, longest_line.probs,
                longest_line.char_probs, longest_line.prob_distributions,
                longest_line.bounding_rect,
                data_hash=longest_line.data_hash,
                conditional_caption_idx=longest_line.conditional_caption_idx
            )
            new_lines[-1] = line
            print('Replacing ', new_lines[-1].text, 'with', line.text)
        else:
            print('2. Appending line', line)
            new_lines.append(line)

        last_line = line

    return new_lines


def _merge_params(params):
    params = [p for p in params if p is not None]

    merged_params = []
    if len(params) == 0:
        return merged_params

    for _ in params[0]:
        merged_params.append({})

    for p in params:
        for i, param in enumerate(p):
            merged_params[i].update(param)

    return merged_params


def get_video_paths(show_name=None, from_folder=None, videos_path=None, file_type='hanzi', return_all_ocr_params=False):
    videos = []

    show_data = None
    video_ids = None
    if show_name is not None:
        with open(f'data/git/shows/{show_name}.json') as f:
            show_data = json.load(f)
            video_ids = []
            for season in show_data['seasons']:
                for episode in season['episodes']:
                    if 'id' in episode:
                        video_ids.append(episode['id'])

    if from_folder is not None:
        if video_ids is None:
            for file_path in os.listdir(from_folder):
                if file_path.endswith('.merkl'):
                    continue
                video_id = os.path.basename(file_path).split('.')[0]
                videos.append((video_id, os.path.join(from_folder, file_path)))
        else:
            for video_id in video_ids:
                if file_type is None:
                    file_path = os.path.join(from_folder, f'{video_id}.json')
                else:
                    file_path = os.path.join(from_folder, f'{video_id}-{file_type}.json')

                videos.append((video_id, file_path))
    elif videos_path is not None:
        assert show_name is not None
        for video_id in video_ids:
            for fmt in ['mkv', 'webm', 'mp4']:
                video_path = os.path.join(videos_path, show_name, video_id + '.' + fmt)
                if os.path.exists(video_path):
                    break
            else:
                video_path = None

            if video_path is None:
                print(f'Found no video for id {video_id}')
                continue

            videos.append((video_id, video_path))

    if show_data is not None:
        ocr_params = []
        for season in show_data['seasons']:
            for episode in season['episodes']:
                if 'id' not in episode:
                    continue

                episode_ocr_params = _merge_params([
                    show_data.get('ocr_params', None),
                    season.get('ocr_params', None),
                    episode.get('ocr_params', None),
                ])

                # Also allow defining "global" parameters outside of ocr_params, directly in the episode/season/show:
                OCR_PARAMS = [
                    'start_time', 'caption_top', 'caption_bottom', 'caption_left',
                    'caption_right', 'refine_bounding_rect', 'ocr_engine', 'use_bert_prior'
                ]
                for param_name in OCR_PARAMS:
                    val = (
                        episode.get(param_name, None) or
                        season.get(param_name, None) or
                        show_data.get(param_name, None)
                    )
                    if val is not None:
                        for _p in episode_ocr_params:
                            _p[param_name] = val

                ocr_params.append(episode_ocr_params)

        out = []
        for (video_id, file_path), params in zip(videos, ocr_params):
            file_path_type = None
            for t in ['english', 'pinyin', 'hanzi']:
                if file_path.endswith(f'-{t}.json'):
                    file_path_type = t

            ps = []
            if params is not None:
                for param in params:
                    if return_all_ocr_params or file_path_type is None or ('type' in param and param['type'] == file_path_type):
                        ps.append(param)

            out.append((video_id, file_path, ps))

        return out

    return videos


def _store_cedict(cedict_with_freqs):
    cedict_with_freqs >> 'data/remote/private/cedict_with_freqs.json'


def make_pinyin_db_classifiers():
    pinyin_freq_db = make_pinyin_freq_db()
    pinyin_freq_db >> 'data/remote/private/pinyin_freqs.json'
    pinyin_classifiers = train_pinyin_classifiers(pinyin_freq_db)
    pinyin_classifiers >> 'data/git/pinyin_classifiers.py'
    cedict_with_freqs = make_cedict(freqs=pinyin_freq_db)
    _store_cedict(cedict_with_freqs)
    return pinyin_freq_db, pinyin_classifiers, cedict_with_freqs


def make_cedict_db():
    pinyin_freq_db = Future.from_file('data/remote/private/pinyin_freqs.json')
    cedict_with_freqs = make_cedict(freqs=pinyin_freq_db)
    _store_cedict(cedict_with_freqs)
    return cedict_with_freqs


@task(serializer=json)
def _make_public_cedict(cedict):
    out = {}
    for sm, (_, entries, *_) in cedict.items():
        out_items = []
        for tr, py, transl, freq, difficulty in entries:
            py_parts = extract_normalized_pinyin(py)
            py_parts_diacriticals = [normalized_to_diacritical(pp) for pp in py_parts]
            out_items.append((tr, py_parts, py_parts_diacriticals, transl.split('/')))

        out[sm] = out_items

    return out


def make_public_cedict_db():
    cedict = make_cedict(freqs=None, filename='data/remote/public/cedict_ts.u8')
    public_cedict = _make_public_cedict(cedict)
    public_cedict >> f'data/remote/public/public_cedict-{public_cedict.hash}.json'

    public_cedict.on_completed = partial(write_hash_file, filename=f'data/remote/public/public_cedict.hash', hash=public_cedict.hash)

    return public_cedict


def process_show_captions(
    show_name: str,
    videos_path: str,
    *,
    force_redo: bool = False,
    video_id: str = None,
):
    os.makedirs('data/remote/private/caption_data/raw_captions', exist_ok=True)
    os.makedirs('data/remote/private/caption_data/meta_trimmed_captions', exist_ok=True)
    videos = get_video_paths(show_name=show_name, videos_path=videos_path)

    out = []
    for (vid, video_path, params) in videos:
        if video_id is not None and video_id != vid:
            continue

        video_length, _, frame_size = get_video_length_size(video_path)

        prev_captions = defaultdict(lambda: None)
        prev_params = defaultdict(lambda: None)
        for param in params:
            if 'caption_top' not in param:
                # It's params for downloaded vtt captions, not OCR

                vtt_types = None
                if param['type'] == 'hanzi':
                    vtt_types = ['zh', 'zh-Hans', 'zh-CN']
                elif param['type'] == 'english':
                    vtt_types = ['en', 'en-US', 'en-UK', 'en-GB']

                for vtt_type in vtt_types:
                    path = f'data/remote/private/caption_data/translations/{vid}.{vtt_type}.vtt'
                    if os.path.exists(path):
                        json_captions = convert_vtt_to_caption_format(path, params, video_length, frame_size)
                        meta_captions = add_metadata(json_captions, vid, show_name)
                        meta_captions >> f'data/remote/private/caption_data/raw_captions/{vid}-{param["type"]}.json'
                        meta_captions >> f'data/remote/private/caption_data/meta_trimmed_captions/{vid}-{param["type"]}.json'
                        out.append(meta_captions)
                        break
                continue

            param_id = param.get('id', None) or param['type']
            depends_on = param.get('depends_on', None)
            action = param.get('action', None)
            conditional_captions, conditional_params = None, None
            if depends_on is not None:
                conditional_captions = prev_captions[depends_on]
                conditional_params = prev_params[depends_on]

            captions, frame_size = extract_video_captions(
                video_path,
                vid,
                param['caption_top'],
                param['caption_bottom'],
                param.get('caption_left', 0.0),
                param.get('caption_right', 1.0),
                param.get('start_time', None),
                param.get('end_time', None),
                replace_levenshtein_threshold=1.0,
                filter_out_too_many_low_prob_chars=param.get('filter_out_too_many_low_prob_chars', True),
                caption_type=param['type'],
                ocr_engine=param.get('ocr_engine', 'cnocr' if param['type'] == 'hanzi' else 'easyocr'),
                use_bert_prior=param.get('use_bert_prior', False),
                conditional_captions=conditional_captions,
                refine_bounding_rect=param.get('refine_bounding_rect', False),
                height_buffer_px=param.get('height_buffer_px', 0),
                screen_recording_video_timings=param.get('screen_recording_video_timings', None),
            )

            if param.get('fade_in_out', False) is True:
                captions = fix_fade(captions)

            json_captions = caption_lines_to_json(captions, frame_size, param, video_length, conditional_params)
            json_captions >> f'data/remote/private/caption_data/raw_captions/{vid}-{param_id}.json'

            if depends_on is not None:
                json_captions_joined = update_conditional_captions(json_captions, conditional_captions, action)
                json_captions_joined >> f'data/remote/private/caption_data/raw_captions/{vid}-{param["type"]}.json'
            else:
                json_captions_joined = json_captions

            meta_captions = add_metadata(json_captions_joined, vid, show_name)
            trimmed_captions = trim_bad_captions(meta_captions)
            trimmed_captions >> f'data/remote/private/caption_data/meta_trimmed_captions/{vid}-{param["type"]}.json'

            prev_captions[param_id] = trimmed_captions
            prev_params[param_id] = param
            if force_redo:
                json_captions.clear_cache()
                json_captions_joined.clear_cache()
                trimmed_captions.clear_cache(delete_output_files=True)
                meta_captions.clear_cache(delete_output_files=True)
                captions.clear_cache(delete_output_files=True)

            out.append(trimmed_captions)

    return out


@task(serializer=json)
def _sum(arr):
    return sum(arr, [])


def make_names_list():
    os.makedirs('data/remote/private/caption_data/captions_all_translations', exist_ok=True)
    videos = get_video_paths(from_folder='data/remote/private/caption_data/captions_all_translations/')
    all_names = []
    for video_id, file_path in videos:
        json_captions_all_translations = Future.from_file(file_path)
        names = collect_names(json_captions_all_translations)
        all_names.append(names)

    names = _sum(all_names)
    names >> 'data/remote/private/names.json'
    return names


def process_translations(
    show_name=None,
    *,
    remove_unmatched_captions: bool=True,
    force_redo: bool=False,
    video_id: str=None
):
    os.makedirs('data/remote/private/caption_data/captions_human_translations', exist_ok=True)
    os.makedirs('data/remote/private/caption_data/machine_translations', exist_ok=True)
    os.makedirs('data/remote/private/caption_data/captions_all_translations', exist_ok=True)

    videos = get_video_paths(show_name=show_name, from_folder='data/remote/private/caption_data/meta_trimmed_captions/', return_all_ocr_params=True)
    out = []
    for vid, file_path, params in videos:
        if video_id is not None and vid != video_id:
            continue
        try:
            trimmed_captions = Future.from_file(file_path)
        except FileNotFoundError:
            continue
        human_translations_paths = [
            f'data/remote/private/caption_data/translations/{vid}.en.vtt',
            f'data/remote/private/caption_data/translations/{vid}.en-US.vtt'
        ]
        human_translations = None
        for path in human_translations_paths:
            if os.path.exists(path):
                human_translations = convert_vtt_to_caption_format(path)

        if human_translations is None:
            english_path = f'data/remote/private/caption_data/raw_captions/{vid}-english.json'
            if os.path.exists(english_path):
                human_translations = Future.from_file(english_path)

        json_captions_human_translations = add_human_translations_merge_lines(trimmed_captions, params, human_translations, remove_unmatched_captions)
        json_captions_human_translations >> f'data/remote/private/caption_data/captions_human_translations/{vid}.json'
        machine_translations = get_machine_translations(json_captions_human_translations)
        machine_translations >> f'data/remote/private/caption_data/machine_translations/{vid}.json'
        json_captions_all_translations = add_machine_translations(json_captions_human_translations, machine_translations)
        json_captions_all_translations >> f'data/remote/private/caption_data/captions_all_translations/{vid}.json'
        if force_redo:
            trimmed_captions.clear_cache()
            json_captions_human_translations.clear_cache(delete_output_files=True)
            machine_translations.clear_cache(delete_output_files=True)
            json_captions_all_translations.clear_cache(delete_output_files=True)
        out.append(json_captions_all_translations)

    return out


def _get_show_fixed_translations(show_name):
    with open(f'data/git/shows/{show_name}.json') as f:
        show_data = json.load(f)

    return show_data.get('fixed_translations', {})


def process_segmentation_alignment(show_name=None, *, force_redo=False, video_id:str=None):
    os.makedirs('data/remote/private/caption_data/alignment_translations', exist_ok=True)
    os.makedirs('data/remote/public/subtitles/', exist_ok=True)

    videos = get_video_paths(show_name=show_name, from_folder='data/remote/private/caption_data/captions_all_translations/', file_type=None)
    show_fixed_translations = _get_show_fixed_translations(show_name)
    pinyin_freq_db = Future.from_file('data/remote/private/pinyin_freqs.json')
    global_known_names = Future.from_file('data/remote/private/names.json')

    out = []
    for vid, file_path, params in videos:
        if video_id is not None and vid != video_id:
            continue
        try:
            json_captions_all_translations = Future.from_file(file_path)
        except FileNotFoundError:
            continue
        alignment_translations = get_alignment_translations(json_captions_all_translations, global_known_names, show_fixed_translations)
        alignment_translations >> f'data/remote/private/caption_data/alignment_translations/{vid}.json'
        json_captions_final = add_segmentation_and_alignment(json_captions_all_translations, alignment_translations, show_fixed_translations)
        json_captions_final >> f'data/remote/public/subtitles/{vid}-{json_captions_final.hash}.json'
        if force_redo:
            alignment_translations.clear_cache(delete_output_files=True)
            json_captions_final.clear_cache(delete_output_files=True)

        json_captions_final.on_completed = partial(write_hash_file, filename=f'data/remote/public/subtitles/{vid}.hash', hash=json_captions_final.hash)
        out.append(json_captions_final)

    return out
