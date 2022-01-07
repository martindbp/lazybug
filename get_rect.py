import sys
import cv2
import numpy as np

def print_y(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(y)

cv2.namedWindow('frame')
cv2.setMouseCallback('frame', print_y)

time_offset = 0 if len(sys.argv) <= 2 else int(sys.argv[2])

cap = cv2.VideoCapture(sys.argv[1])
cap.set(cv2.CAP_PROP_POS_MSEC, time_offset*1000)

while cap.isOpened():
    ret, frame = cap.read()
    cv2.imshow('frame', frame)
    key = cv2.waitKey()

cap.release()
cv2.destroyAllWindows()
