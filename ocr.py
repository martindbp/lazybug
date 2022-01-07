"""
* text has to go from left to right -> if there are blobs to the left, but not the whole way, then no captions
    only holds for non-centered text
//* remove blobs that intersect crop
//* remove small blobs
//* remove large blobs

** Use adaptive threshold components for detecting timing, but use normal thresholding for OCR
** Take all components we've decided are characters, join them and any black space around it, do in-painting and then do OCR on that image
"""
from cnocr import CnOcr
import numpy as np
import cv2

DEBUG = False
ocr = CnOcr(model_name='densenet-lite-gru')

ui = None
thres = None
contour_index_map = None
contours, hierarchy = None, None
selected_contours = set()

cv2.namedWindow("frame")

KERNEL_SIZES = [3, 5, 7, 9, 11, 13, 15, 17, 19]
MIN_AREA = 2*2
MAX_AREA = 50*50

caption_top, caption_bottom, caption_left = 900, 980, 147
adaptive_kernel_size_idx, adaptive_c = 3, 5
use_channel = 'gray'
range_start, range_end = 220, 256
#frame_offset = 30*1962
frame_offset = 0
cap = cv2.VideoCapture('waikefengyun.mkv')

#use_channel = 'b'
#adaptive_kernel_size_idx, adaptive_c = 3, 5
#frame_offset = 30*60
#cap = cv2.VideoCapture('mandarincorner.mkv')

#caption_top, caption_bottom, caption_left = 915, 987, 147
#adaptive_kernel_size_idx, adaptive_c = 3, 2
#use_channel = 'gray'
#range_start, range_end = 230, 256
#frame_offset = 30*1500
#cap = cv2.VideoCapture('feicheng.mp4')


#use_channel = 'gray'
#adaptive_kernel_size_idx, adaptive_c = 3, 5
#frame_offset = 30*60
#cap = cv2.VideoCapture('peppa.mkv')

frame = None

saved_pixels = []

def get_num_parents(hierarchy, i):
    num_parents = 0
    while hierarchy[0][i][3] >= 0:
        num_parents += 1
        i = hierarchy[0][i][3]  # parent

    return num_parents


def click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        contour_index = contour_index_map[y, x]
        if contour_index < 0:
            print('clicked black')
            return
        print('clicked contour nr', contour_index)
        if contour_index in selected_contours:
            selected_contours.remove(contour_index)
        else:
            selected_contours.add(contour_index)

        draw_picker_ui()

cv2.setMouseCallback("frame", click)

def draw_picker_ui():
    global ui
    ui = frame.copy()

    for selected_idx in selected_contours:
        cv2.drawContours(ui, contours, selected_idx, (255,0,0), -1, hierarchy=hierarchy, maxLevel=1)

    cv2.imshow('frame', ui)


def predict_chars(mask, window_buffer=10):
    ys, xs = np.where(mask > 0)
    x_max, x_min = xs.max()+1, xs.min()
    y_max, y_min = ys.max()+1, ys.min()
    mask_crop = mask[y_min:y_max, x_min:x_max]

    larger = np.zeros((mask_crop.shape[0]+2*window_buffer, mask_crop.shape[1]+2*window_buffer), 'uint8')
    larger[window_buffer:-window_buffer, window_buffer:-window_buffer] = mask_crop
    larger = 255 - larger
    res = ocr.ocr(larger)
    return res


def filter_contours_caption_area(caption_area):
    contours, hierarchy = cv2.findContours(caption_area, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    components = np.zeros_like(caption_area)
    for i, contour in enumerate(contours):
        if get_num_parents(hierarchy, i) % 2 != 0:
            continue

        area = cv2.contourArea(contour)
        if area <= MIN_AREA or area >= MAX_AREA:
            continue
        contour = contour.reshape(-1, 2)
        xs = contour[:, 0]
        ys = contour[:, 1]
        x_max, x_min = xs.max()+1, xs.min()
        y_max, y_min = ys.max()+1, ys.min()

        if x_min == 0 or y_min == 0 or x_max == caption_area.shape[1] or y_max == caption_area.shape[0]:
            continue

        cv2.drawContours(components, contours, i, 255, -1, hierarchy=hierarchy)

    return components


def srt_timestamp(t):
    hours = int(t // (60*60))
    t -= hours * 60 * 60
    minutes = int(t // 60)
    t -= minutes * 60
    seconds = t
    return f'{hours:02}:{minutes:02}:{seconds:.3f}'.replace('.', ',')


cap.set(cv2.CAP_PROP_POS_FRAMES, frame_offset)

set_new_value = False
last_components = None
caption_idx, current_caption, current_caption_time = 1, None, None
out_file = open('out.srt', 'w')
while cap.isOpened():
    if not set_new_value:
        ret, frame = cap.read()

    if set_new_value:
        print('adaptive_c', adaptive_c)
        print('adaptive_kernel_size', KERNEL_SIZES[adaptive_kernel_size_idx])
        set_new_value = False

    if use_channel in ['H', 'S', 'V']:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        channel = hsv[..., ['H', 'S', 'V'].index(use_channel)]
        if DEBUG:
            cv2.imshow('HSV', channel)
    elif use_channel in ['L', 'a', 'b']:
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2Lab)
        channel = lab[..., ['L', 'a', 'b'].index(use_channel)]
        if DEBUG:
            cv2.imshow('Lab', channel)
    else:
        channel = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    thres = 255*((channel > range_start) & (channel < range_end)).astype('uint8')
    #adaptive_kernel_size = KERNEL_SIZES[adaptive_kernel_size_idx]
    #adaptive_thres = cv2.adaptiveThreshold(
        #channel,
        #255,
        #cv2.ADAPTIVE_THRESH_MEAN_C,
        #cv2.THRESH_BINARY,
        #adaptive_kernel_size,
        #adaptive_c
    #)
    caption_area = thres[caption_top:caption_bottom, caption_left:]
    #adaptive_caption_area = adaptive_thres[caption_top:caption_bottom, caption_left:]

    components = filter_contours_caption_area(caption_area)

    if last_components is not None:
        diff = components ^ last_components
        diff_num = diff.sum() / 255
        has_text = components.sum() > 1000
        has_changed = diff_num > 2000
        curr_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000

        if has_changed and current_caption is not None:
            out_file.write(f'{caption_idx}\n')
            out_file.write(f'{srt_timestamp(current_caption_time)} --> {srt_timestamp(curr_time)}\n')
            out_file.write(f'{current_caption}\n\n')
            out_file.flush()
            print(current_caption)
            caption_idx += 1
            current_caption, current_caption_time = None, None

        if has_changed and has_text:
            lines = predict_chars(components)
            if len(lines) >= 1:
                line = ''.join(predict_chars(components)[0])
                current_caption = line
                current_caption_time = curr_time

    last_components = components
    #adaptive_components = filter_contours_caption_area(adaptive_caption_area)
    #adaptive_components = 255 * ((adaptive_components > 0) & (components > 0)).astype('uint8')

    #cv2.imshow('frame', frame)
    #cv2.waitKey(1)
    if DEBUG:
        cv2.imshow('caption area', caption_area)
        cv2.imshow('adaptive caption area', adaptive_caption_area)
        cv2.imshow('components', components)
        #cv2.imshow('adaptive_components', adaptive_components)
        key = cv2.waitKey()
        if key & 0xFF == ord('c'):
            adaptive_c = (adaptive_c + 1) % 10
            set_new_value = True

        if key & 0xFF == ord('k'):
            adaptive_kernel_size_idx = (adaptive_kernel_size_idx + 1) % len(KERNEL_SIZES)
            set_new_value = True

out_file.close()

cap.release()
cv2.destroyAllWindows()
