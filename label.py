from cnocr import CnOcr
import numpy as np
import cv2

ocr = CnOcr()

ui = None
thres = None
contour_index_map = None
contours, hierarchy = None, None
selected_contours = set()

cv2.namedWindow("frame")

#use_channel = 'gray'
#frame_offset = 30*1962
#cap = cv2.VideoCapture('waikefengyun.mkv')

use_channel = 'b'
frame_offset = 30*60
cap = cv2.VideoCapture('mandarincorner.mkv')

#use_channel = 'gray'
#frame_offset = 30*1500
#cap = cv2.VideoCapture('feicheng.mp4')


#use_channel = 'gray'
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
    #ui = np.zeros((*thres.shape, 3), 'uint8')
    ui = frame.copy()
    #cv2.drawContours(ui, contours, -1, (255,255,255), -1, hierarchy=hierarchy)

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


cap.set(cv2.CAP_PROP_POS_FRAMES, frame_offset)

def pmf(pixels_samples):
    bins = 40
    histogram = np.zeros((255 // bins + 1, 255 // bins + 1, 255 // bins + 1), float)
    total = 0
    for pixels in pixels_samples:
        for pixel in pixels:
            histogram[pixel[0] // bins, pixel[1] // bins, pixel[2] // bins] += 1
        total += len(pixels)

    return histogram / total


while cap.isOpened():
    ret, frame = cap.read()
    cv2.imshow('frame', frame)
    #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    #gray_thres = 255 * (gray > 230).astype('uint8')
    #cv2.imshow('gray_thres', gray_thres)

    key = cv2.waitKey()

    if key & 0xFF != ord('r'):
        continue

    print('thresholding')
    if use_channel in ['H', 'S', 'V']:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        channel = hsv[..., ['H', 'S', 'V'].index(use_channel)]
        cv2.imshow('HSV', channel)
        #cv2.waitKey()
    elif use_channel in ['L', 'a', 'b']:
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2Lab)
        channel = lab[..., ['L', 'a', 'b'].index(use_channel)]
        cv2.imshow('Lab', channel)
        #cv2.waitKey()
    else:
        channel = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    thres = cv2.adaptiveThreshold(channel, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 5)
    #cv2.imshow('thres', thres)
    #cv2.waitKey()

    print('find contours')
    contours, hierarchy = cv2.findContours(thres, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros(frame.shape[:2], 'uint8')
    contour_index_map = -1 * np.ones(frame.shape[:2], 'int16')
    max_rgb = 0
    print('draw index map')

    pixels_pmf = None
    if len(saved_pixels) > 0:
        pixels_pmf = pmf(saved_pixels)

    for i, contour in enumerate(contours):
        if get_num_parents(hierarchy, i) % 2 != 0:
            continue

        if cv2.contourArea(contour) > 50*50:
            continue

        contour = contour.reshape(-1, 2)
        xs = contour[:, 0]
        ys = contour[:, 1]
        x_max, x_min = xs.max()+1, xs.min()
        y_max, y_min = ys.max()+1, ys.min()
        mask_crop = np.zeros((y_max-y_min, x_max-x_min), 'uint8')
        contour_index_crop = -1 * np.ones((y_max-y_min, x_max-x_min), 'int16')
        offset = np.array([x_min, y_min])
        contours_crop = [contour-offset for contour in contours]
        cv2.drawContours(mask_crop, contours_crop, i, 255, -1, hierarchy=hierarchy)

        cv2.drawContours(contour_index_crop, contours_crop, i, i, -1, hierarchy=hierarchy)
        contour_index_map[y_min:y_max, x_min:x_max][mask_crop > 0] = contour_index_crop[mask_crop > 0]

        if pixels_pmf is not None:
            mask_crop_eroded = cv2.erode(mask_crop, np.ones((3, 3), np.uint8))
            if mask_crop_eroded.sum() == 0:
                mask_crop_eroded = mask_crop
            contour_pixels = frame[y_min:y_max, x_min:x_max][mask_crop_eroded > 0]
            contour_pmf = pmf([contour_pixels])
            diff = np.abs(contour_pmf - pixels_pmf).sum()
            kl_div = contour_pmf * np.log(contour_pmf / np.maximum(pixels_pmf, 10e-10))
            kl_div[contour_pmf == 0] = 0
            kl_div = kl_div.sum()
            print(kl_div)
            if kl_div < 2:
                selected_contours.add(i)


    draw_picker_ui()
    cv2.waitKey()

    selected_mask = np.zeros(thres.shape, 'uint8')
    for selected_idx in selected_contours:
        cv2.drawContours(selected_mask, contours, selected_idx, 255, -1, hierarchy=hierarchy, maxLevel=1)

    print(predict_chars(selected_mask))

    pixels = frame[selected_mask > 0]
    saved_pixels.append(pixels)
    contour_index_map = None
    contours, hierarchy = None, None
    selected_contours = set()

cap.release()
cv2.destroyAllWindows()
