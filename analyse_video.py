# -*- coding: utf-8 -*-
import numpy as np
import cv2
import subprocess
import os
import sys
import optparse

try:
    sys.setdefaultencoding('utf-8')
except:
    pass

python_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
currPath = sys.path[0]
highPath = os.path.split(currPath)[0]
env = os.environ.copy()
spliter = ';' if os.name == 'nt' else ':'
env["PATH"] = python_dir + spliter + highPath + spliter + env["PATH"]

pattern0_f = python_dir + "/usr/pattern0.png"
if (not os.path.isfile(pattern0_f)):
    pattern0_f = highPath + "/usr/pattern0.png"
if (not os.path.isfile(pattern0_f)):
    print("Can not load nmtg pattern0" + pattern0_f)
img_pattern0 = cv2.imread(pattern0_f)

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
parser.add_option('--nmtg_tm_threshold',
                  action="store", dest="nmtg_tm_threshold",
                  help="nmtg box template matching threshold", default=0.12)


options, args = parser.parse_args()
if (not len(args)):
    print("Missing input video.")
    exit(-1)
inputvideo = os.path.abspath(args[0])
if (not os.path.isfile(inputvideo)):
    print("Can not open video file " + inputvideo)
    exit(-1)

# output dir
print("Inputvideo: " + inputvideo)
basename = os.path.basename(inputvideo)
dirname = os.path.dirname(inputvideo)
output_dir = dirname + ('/' if dirname else '') + 'autosub'

# re encode
reencode_video_name = inputvideo + '_reencode.mp4'
print("Re encode to CFR Video file: " + inputvideo)
ffcmd = "ffmpeg -hide_banner -y -i " + inputvideo + \
    " -c:v mpeg4 -b:v 24000k -r 30 -s 1280x720 -acodec aac -strict -2 -ac 2 -ab 256k -ar 44100 -f mp4 " + reencode_video_name
" aac -strict -2 -ac 2 -ab 256k -ar 44100 -f "
print("Invoking: " + ffcmd)
subprocess.call(ffcmd, shell=True, env=env)
print("Re-encoding Finished")

script_output = output_dir + '/' + basename + '.krfss'
img_output_dir = output_dir + '/' + basename + '_img'
print("Script output: " + script_output)
print("Image output directory: " + img_output_dir)

os.makedirs(output_dir, exist_ok=True)
os.makedirs(img_output_dir, exist_ok=True)

# timestamp array
timestamp_data = []
# nmtg_db (array of image)
g_nmtg_img_db = []
# raw_nmtg_index -> db_index
nmtg_map = []

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

# judge if two nmtg_img are same


def is_same_name(img0, img1):
    kernel = np.ones((3, 3), np.uint8)
    img0_dil_inv = cv2.bitwise_not(cv2.dilate(img0, kernel, iterations=1))
    img1_dil_inv = cv2.bitwise_not(cv2.dilate(img1, kernel, iterations=1))
    img_judge0 = cv2.bitwise_and(img0, img1_dil_inv)
    img_judge1 = cv2.bitwise_and(img1, img0_dil_inv)
    return 0 == np.sum(img_judge0) + np.sum(img_judge1)

# get_index in nmtg db
# if no same name in the db
# then append


def get_nmtg_index(img1):
    for (i, img0) in enumerate(g_nmtg_img_db):
        if is_same_name(img0, img1):
            return i
    g_nmtg_img_db.append(img1.copy())
    i = len(g_nmtg_img_db) - 1
    cv2.imwrite(img_output_dir + '/' + "/nmtg_" + ("%04d" % i)+".png", img1)
    return i


# POSITION DEFINITION
ROI = (slice(500, 710), slice(70, 1140))
ROI_JUDGE0 = (slice(70, 72), slice(130, 1000))
ROI_JUDGE1 = (slice(178, 180), slice(130, 1000))
ROI_NMTG = (slice(7, 50), slice(15, 395))
ROI_NMTG_SEARCH = (slice(0, 210), slice(13, 13 + 382))
LINE_START = 169
LINE_LENGTH = 800
LINE_HEIGHT = 36
ROI_LINE0_Y = 84
ROI_LINE1_Y = 136
ROI_LINE0 = (slice(ROI_LINE0_Y, ROI_LINE0_Y + LINE_HEIGHT),
             slice(LINE_START, LINE_START + LINE_LENGTH))
ROI_LINE1 = (slice(ROI_LINE1_Y, ROI_LINE1_Y + LINE_HEIGHT),
             slice(LINE_START, LINE_START + LINE_LENGTH))

# input video
video_name = reencode_video_name
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
    if (video.get(cv2.CAP_PROP_FRAME_HEIGHT) > video.get(cv2.CAP_PROP_FRAME_WIDTH)):
        img_rot = np.rot90(img)
    else:
        img_rot = img
    # ROI of TextArea and NameTag
    img_crop = img_rot[ROI]
    # Judge ROI of TextArea
    img_judge0 = img_crop[ROI_JUDGE0]
    img_judge1 = img_crop[ROI_JUDGE1]
    # TextArea exist?
    is_blank = is_blank_func(img_judge0, img_judge1)

    # binarization
    img_gray = cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY)
    retval, img_bin = cv2.threshold(img_gray, int(
        options.gray_threshold), 255, cv2.THRESH_BINARY)

    # Invert NameTag Area
    img_nmtg = cv2.bitwise_not(img_bin[ROI_NMTG])
    # The fisrt line of TextArea
    img_line0 = img_bin[ROI_LINE0]
    # The second line of TextArea
    img_line1 = img_bin[ROI_LINE1]
    # Concat 2 lines horizontally
    img_line = np.concatenate((img_line0, img_line1), axis=1)

    img_line0_color = img_crop[ROI_LINE0]
    img_line1_color = img_crop[ROI_LINE1]
    img_line0_color = cv2.bitwise_or(
        img_line0_color, cv2.cvtColor(img_line0, cv2.COLOR_GRAY2BGR))
    img_line1_color = cv2.bitwise_or(
        img_line1_color, cv2.cvtColor(img_line1, cv2.COLOR_GRAY2BGR))
    if (frame == 1):
        img_line_color = np.concatenate(
            (img_line0_color, img_line1_color), axis=0)

    # Template Matching for NMTG
    (h, w, c) = img_pattern0.shape
    img_tm = cv2.matchTemplate(
        img_crop[ROI_NMTG_SEARCH], img_pattern0, cv2.TM_SQDIFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(img_tm)
    if (min_val < float(options.nmtg_tm_threshold)):
        nmtg_y = min_loc[1]
        if (min_loc[1] > 1):
            print("Nmtg Transition", frame, nmtg_y)
            timestamp_data.append(
                {"at": frame, "action": "N", "y": nmtg_y}
            )

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
            print("TextArea In", frame)
            timestamp_data.append({"at": frame, "action": "T"})
        else:
            print("TextArea Out", frame)
            timestamp_data.append({"at": frame, "action": "X"})
        is_blank_last = int(is_blank)

    # NO TEXT, waiting for a new line
    if (status == 0):
        # Start of a Line
        if (textpos > 0):
            print("LN", frame)
            timestamp_data.append({"at": frame, "action": "L"})
            # Status -> 1
            status = 1
            # mark frame change
            last_change = frame
            last_textpos_store = 0
            if (storing == 0):
                print("Start", frame)
                timestamp_data.append(
                    {"at": frame, "action": "S", "sub": index_sub})
                storing = 1

    # Monitoring change of textarea
    elif (status == 1):
        # new text +
        if (is_textpos_changed > 0):
            last_change = frame
            if (storing == 0):
                print("Start", frame)
                timestamp_data.append(
                    {"at": frame, "action": "S", "sub": index_sub})
                storing = 1
        # Keep
        if (is_textpos_changed == 0):
            # wait <wait_frame_threshold> and then store.
            if (frame - last_change > int(options.wait_frame_threshold) and abs(last_textpos_store - textpos) > int(options.textpos_threshold)):
                frame_real = frame - int(options.wait_frame_threshold)
                print("End", frame_real)
                timestamp_data.append(
                    {"at": frame_real, "action": "E", "sub": index_sub})
                storing = 0
                # Store TextArea
                img_line0_color_c = img_line0_color.copy()
                img_line1_color_c = img_line1_color.copy()
                cv2.line(img_line0_color_c,
                         (last_textpos_store + 10, 30), (textpos, 30),
                         (127, 255, 0), 20)
                cv2.line(img_line1_color_c,
                         (last_textpos_store + 10 - LINE_LENGTH,
                          30), (textpos - LINE_LENGTH, 30),
                         (127, 255, 0), 20)
                img_line_color_o = np.concatenate(
                    (img_line0_color, img_line1_color), axis=0)
                img_line_color_c = np.concatenate(
                    (img_line0_color_c, img_line1_color_c), axis=0)
                img_line_color = cv2.addWeighted(
                    img_line_color_o, 0.85, img_line_color_c, 0.15, 1)
                cv2.imwrite(img_output_dir + '/' + "text_" +
                            ("%04d" % index_sub)+".png", img_line_color)
                print("index_sub: " + str(index_sub))

                # Store NameTag
                nmtg_index = get_nmtg_index(img_nmtg)
                nmtg_map.append(nmtg_index)
                print("nmtg_index: " + str(nmtg_index))

                index_sub += 1
                last_textpos_store = textpos

        # Carriage return
        if (is_textpos_changed < 0):
            print("CR", frame)
            timestamp_data.append({"at": frame, "action": "C"})
            status = 0

    cv2.imshow("img_crop", img_crop)
    cv2.imshow("img_sub", img_line_color)
    cv2.waitKey(1)
    last_textpos = textpos

print("All End", frame)
video.release()
timestamp_data.append({"at": frame, "action": "O"})

# Write to json file
import json
script_fp = open(script_output, mode='w', encoding='utf-8')
json_nmtgs = [''] * len(g_nmtg_img_db)
json_trans = [''] * len(nmtg_map)
json_data = {
    "video": basename,
    "total": len(nmtg_map),
    "lang": '',
    "nmtgs": json_nmtgs,
    "trans": json_trans,
    "nmtg_map": nmtg_map,
    "timestamp": timestamp_data
}
json_text = json.dumps(json_data, indent=2)
script_fp.write(json_text)
