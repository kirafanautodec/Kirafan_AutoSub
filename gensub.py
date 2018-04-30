# -*- coding: utf-8 -*-
import numpy as np
import cv2
import subprocess
import os
import optparse

# Parse options
parser = optparse.OptionParser()
parser.add_option('-i', '--input',
    action="store", dest="input",
    help="input file of video file")
parser.add_option('--gray_threshold',
    action="store", dest="gray_threshold",
    help="gray_threshold of binarization", default=160)
parser.add_option('--textpos_threshold',
    action="store", dest="textpos_threshold",
    help="text position detection threshold", default=5)
parser.add_option('--wait_frame_threshold',
    action="store", dest="wait_frame_threshold",
    help="text pause detection threshold in frame", default=2)

options, args = parser.parse_args()
if (not options.input):
    print("Missing argument for option 'i'.")
    exit(-1)
if (not os.path.isfile(options.input)):
    print("Can not open video file " + options.input)
    exit(-1)
    
# output dir
filepwd = options.input + '_autosub'
print("Work directory: " + filepwd)
output = filepwd + '/' + 'img'    
os.makedirs(output, exist_ok=True)

# timestamp file
timestampfn = filepwd + '/timestamp.txt'
timestampfp = open(timestampfn, mode='w', encoding='utf-8')

# COLOR DEFINITION
BLANK_COLOR_MAX = (250, 256, 256)
BLANK_COLOR_MIN = (190, 190, 210)

# blank color of textarea?
def is_blank_p(p):
    return \
            (BLANK_COLOR_MAX[0] > p[0] > BLANK_COLOR_MIN[0]) and \
            (BLANK_COLOR_MAX[1] > p[1] > BLANK_COLOR_MIN[1]) and \
            (BLANK_COLOR_MAX[2] > p[2] > BLANK_COLOR_MIN[2])
            
def is_blank_func(im0, im1):
    i0 = np.asarray(im0)
    i1 = np.asarray(im1)
    for ln in i0:
        for p in ln:
            if not is_blank_p(p):
                return False
    for ln in i1:
        for p in ln:
            if not is_blank_p(p):
                return False
    return True

# POSITION DEFINITION
ROI = (slice(520, 740), slice(80, 1180))
ROI_JUDGE0 = (slice(78, 80), slice(130, 1000))
ROI_JUDGE1 = (slice(183, 185), slice(130, 1000))
ROI_NMTAG = (slice(10, 50), slice(5, 405))
LINE_START = 165
LINE_LENGTH = 835
LINE_HEIGHT = 40
ROI_LINE0 = (slice(88, 88 + LINE_HEIGHT), slice(LINE_START, LINE_START + LINE_LENGTH))
ROI_LINE1 = (slice(143, 143 + LINE_HEIGHT), slice(LINE_START, LINE_START + LINE_LENGTH))

# input video
video_name = options.input
video = cv2.VideoCapture(video_name)
fps = video.get(cv2.CAP_PROP_FPS)
frame = 0

# last character position of textarea
last_textpos = 0
last_change = 0
last_textpos_store = 0

# Status
# 0: No text in textarea, waiting for text
# 1: 
status = 0

# Storing
# 0: waiting for a start point of rolling text
# 1: waiting for a end point of rolling text
storing = 0

# index of subtitle
index_sub = 0

# blank in last frame
is_blank_last = -1

while(video.isOpened()):
    ret, img = video.read()
    if not ret:
        break
    time = frame / fps
    frame += 1

    # Iphone's video is rotated
    img_rot = np.rot90(img)
    # ROI of TextArea and NameTag
    img_crop = img_rot[ROI]
    # Judge ROI of TextArea
    img_judge0 = img_crop[ROI_JUDGE0]
    img_judge1 = img_crop[ROI_JUDGE1]
    # TextArea exist?
    is_blank = is_blank_func(img_judge0, img_judge1)

    # binarization
    img_gray = cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY)
    retval, img_bin = cv2.threshold(img_gray, int(options.gray_threshold), 255, cv2.THRESH_BINARY)

    # Invert NameTag Area
    img_nmtag = cv2.bitwise_not(img_bin[ROI_NMTAG])
    # The fisrt line of TextArea
    img_line0 = img_bin[ROI_LINE0]
    # The second line of TextArea
    img_line1 = img_bin[ROI_LINE1]
    # Concat 2 lines horizontally
    img_line = np.concatenate((img_line0, img_line1), axis=1)
    
    img_line0_color = img_crop[ROI_LINE0]
    img_line1_color = img_crop[ROI_LINE1]
    img_line0_color = cv2.bitwise_or(img_line0_color, cv2.cvtColor(img_line0, cv2.COLOR_GRAY2BGR))
    img_line1_color = cv2.bitwise_or(img_line1_color, cv2.cvtColor(img_line1, cv2.COLOR_GRAY2BGR))
    if (frame == 1):
        img_line_color = np.concatenate((img_line0_color, img_line1_color), axis=0)

    # If TextArea does not exits
    # clear the textarealine
    if (not is_blank):
        img_line[:] = 255

    # Rotated textarea line 90 deg  
    arr_line_rot = np.array(np.rot90(img_line))
    # Scan the 'x position' of last character => textpos        
    textpos = arr_line_rot.shape[0]
    for col in arr_line_rot:
        textpos -= 1
        if (not np.all(col)):
            break

    # detect change of textpos   
    is_textpos_changed = 0
    # avoid jittering of textpos
    if (abs(textpos - last_textpos) > int(options.textpos_threshold)):
        is_textpos_changed = 1 if (textpos - last_textpos) > 0 else -1 

    if (not is_blank_last == int(is_blank)):
        if (is_blank):
            print ("TextArea In", frame)
            timestampfp.write(str(frame) + " T\n")
        else:
            print ("TextArea Out", frame)
            timestampfp.write(str(frame) + " X\n")
        is_blank_last = int(is_blank)
    
    # NO TEXT, waiting for a new line
    if (status == 0):
        # Start of a Line
        if (textpos > 0):
            print ("LN", frame)
            timestampfp.write(str(frame) + " L\n")
            # Status -> 1
            status = 1
            # mark frame change
            last_change = frame
            last_textpos_store = 0
            if (storing == 0):
                print("Start", frame)
                timestampfp.write(str(frame) + " S " + str(index_sub) + "\n")
                storing = 1

    # Monitoring change of textarea
    elif (status == 1):
        # new text + 
        if (is_textpos_changed > 0):
            last_change = frame
            if (storing == 0):
                print("Start", frame)
                timestampfp.write(str(frame) + " S " + str(index_sub) + "\n")
                storing = 1
        # Keep
        if (is_textpos_changed == 0):
            # wait <wait_frame_threshold> and then store.
            if (frame - last_change > int(options.wait_frame_threshold) and not last_textpos_store == textpos):
                frame_real = frame - int(options.wait_frame_threshold)
                print ("End", frame_real)
                timestampfp.write(str(frame_real) + " E " + str(index_sub) + "\n")
                storing = 0
                #img_line_last = img_line[:, last_textpos_store:textpos]
                img_line0_color_c = img_line0_color.copy()
                img_line1_color_c = img_line1_color.copy()
                cv2.line(img_line0_color_c, \
                         (last_textpos_store + 10, 30), (textpos, 30), \
                         (127, 255, 0), 20)
                cv2.line(img_line1_color_c, \
                         (last_textpos_store + 10 - LINE_LENGTH, 30), (textpos - LINE_LENGTH, 30), \
                         (127, 255, 0), 20)
                img_line_color_o = np.concatenate((img_line0_color, img_line1_color), axis=0)
                img_line_color_c = np.concatenate((img_line0_color_c, img_line1_color_c), axis=0)
                img_line_color = cv2.addWeighted(img_line_color_o, 0.85, img_line_color_c, 0.15, 1)
                #img_line_color[:, last_textpos_store:textpos]
                cv2.imwrite(output + "/text_" + ("%04d"%index_sub)+".png", img_line_color)
                cv2.imwrite(output + "/nmtg_" + ("%04d"%index_sub)+".png", img_nmtag)
                index_sub += 1
                last_textpos_store = textpos

        # Carriage return
        if (is_textpos_changed < 0):
            print("CR", frame)
            timestampfp.write(str(frame) + " C\n")
            status = 0    

    cv2.imshow("img_crop", img_crop)
    cv2.imshow("img_sub", img_line_color)
    cv2.waitKey(1)
    last_textpos = textpos

print ("All End", frame)
timestampfp.write(str(frame) + " O\n")
video.release()
