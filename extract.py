import numpy as np
import cv2

ui = None
thres = None
contour_index_map = None
contours, hierarchy = None, None
selected_contours = set()

cv2.namedWindow("frame")

video_dir = '/media/marpett/Data/videos/'

#caption_top = 622
#caption_bottom = 675
#frame_offset = 30*10
#name = 'tw'
#scale = 1
#cap = cv2.VideoCapture(f'{video_dir}/tw.mp4')

#caption_top = 910
#caption_bottom = 960
#frame_offset = 30*30
#name = 'story'
#scale = 1
#cap = cv2.VideoCapture(f'{video_dir}/story.mkv')


#caption_top = 905
#caption_bottom = 972
#frame_offset = 30*(60+15)30*50
#name = 'waike'
#scale = 1
#cap = cv2.VideoCapture(f'{video_dir}/waikefengyun.mkv')


#caption_top = 920
#caption_bottom = 978
#frame_offset = 30*100
#name = 'feicheng'
#scale = 1
#cap = cv2.VideoCapture(f'{video_dir}/feicheng.mp4')



#caption_top = 641
#caption_bottom = 663
#frame_offset = 0
#name = 'legend'
#scale = 1.0
#cap = cv2.VideoCapture(f'{video_dir}/legend.mkv')


#caption_top = 641
#caption_bottom = 663
#frame_offset = 0
#name = 'nichang'
#scale = 1.0
#cap = cv2.VideoCapture(f'{video_dir}/nichang.mp4')


#caption_top = 641
#caption_bottom = 663
#frame_offset = 100*30
#name = 'military'
#scale = 1.0
#cap = cv2.VideoCapture(f'{video_dir}/military.mp4')

#caption_top = 641
#caption_bottom = 663
#frame_offset = 100*30
#name = 'ww2'
#scale = 1.0
#cap = cv2.VideoCapture(f'{video_dir}/ww2.mp4')

#caption_top = 641
#caption_bottom = 663
#frame_offset = 0
#name = 'mingdynasty'
#scale = 1.0
#cap = cv2.VideoCapture(f'{video_dir}/mingdynasty.webm')

#caption_top = 641
#caption_bottom = 663
#frame_offset = 60*30
#name = 'documentary'
#scale = 1.0
#cap = cv2.VideoCapture(f'{video_dir}/documentary.mp4')


caption_top = 641
caption_bottom = 663
frame_offset = 60*30
name = 'kxu1ys2Xy6g'
scale = 1.0
cap = cv2.VideoCapture(f'{video_dir}/kxu1ys2Xy6g.webm')



#caption_top = 641
#caption_bottom = 663
#frame_offset = 0
#name = 'loveintime'
#scale = 1.0
#cap = cv2.VideoCapture(f'{video_dir}/loveintime1.mp4')



#caption_top = 954 * 2
#caption_bottom = 1022 * 2
#frame_offset = 30*10
#name = 'peppa'
#scale = 0.5
#cap = cv2.VideoCapture(f'{video_dir}/peppa.mkv')

#caption_top = 890
#caption_bottom = 963
#frame_offset = 30*60
#name = 'corner'
#scale = 1
#cap = cv2.VideoCapture(f'{video_dir}/corner.mkv')

#caption_top = 953
#caption_bottom = 1008
#frame_offset = 0 #30*60
#name = 'chengxu'
#scale = 1
#cap = cv2.VideoCapture(f'{video_dir}/chengxu.mp4')


#def click(event, x, y, flags, param):
    #if event == cv2.EVENT_LBUTTONDOWN:
        #contour_index = contour_index_map[y, x]
        #if contour_index < 0:
            #print('clicked black')
            #return
        #print('clicked contour nr', contour_index)
        #if contour_index in selected_contours:
            #selected_contours.remove(contour_index)
        #else:
            #selected_contours.add(contour_index)

        #draw_picker_ui()

#cv2.setMouseCallback("frame", click)

#def draw_picker_ui():
    #global ui
    #ui = frame.copy()

    #for selected_idx in selected_contours:
        #cv2.drawContours(ui, contours, selected_idx, (255,0,0), -1, hierarchy=hierarchy, maxLevel=1)

    #cv2.imshow('frame', ui)

cap.set(cv2.CAP_PROP_POS_FRAMES, frame_offset)

i = 0
while cap.isOpened():
    ret, frame = cap.read()
    if scale != 1:
        frame_resized = cv2.resize(frame, (int(frame.shape[1] * scale), int(frame.shape[0] * scale)), interpolation=cv2.INTER_LANCZOS4) 
        cv2.imshow('frame', frame_resized)
    else:
        cv2.imshow('frame', frame)

    key = cv2.waitKey()
    if key & 0xFF == ord('h'):
        # Extract whole frame
        cv2.imwrite(f'{name}_{i}.png', frame)
        i += 1

    if key & 0xFF == ord('c'):
        # First scale it to the right resolution
        scale_factor = 50 / (caption_bottom - caption_top)
        resized = cv2.resize(frame, (int(frame.shape[1] * scale_factor), int(frame.shape[0] * scale_factor)), interpolation=cv2.INTER_LANCZOS4) 
        top_resized = int(caption_top * scale_factor)
        bottom_resized = int(caption_bottom * scale_factor)

        padding = (128 - 50) // 2
        crop = resized[top_resized-padding:bottom_resized+padding, :]
        assert crop.shape[0] == 128
        print(f'{name}_{i}.png')
        cv2.imwrite(f'{name}_{i}.png', crop)
        i += 1

cap.release()
cv2.destroyAllWindows()
