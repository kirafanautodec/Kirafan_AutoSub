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

parser = optparse.OptionParser()
parser.add_option('--start_num',
                  action="store", dest="start_num",
                  help="start num of sub index", default=1)
parser.add_option('--threshold',
                  action="store", dest="threshold",
                  help="color_threshold of detection", default=6)
parser.add_option('--pre_cut',
                  action="store", dest="pre_cut",
                  help="number of frames which will be cut after the starting position of every clip", default=8)
parser.add_option('--sub_cut',
                  action="store", dest="sub_cut",
                  help="number of frames which will be cut before the end position of every clip", default=0)
parser.add_option('-r', '--report',
                  action="store", dest="report",
                  help="progress report intervals", default=10)

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
output_dir = dirname + ('/' if dirname else '') + basename + '_seq_video/'

# re encode
reencode_video_name = inputvideo + '_tmp_thumbnail.mp4'
print("Re encode to CFR Video file: " + inputvideo)
ffcmd = "ffmpeg -hide_banner -loglevel error -stats -y -i " + inputvideo + \
    " -c:v h264 -preset ultrafast -r 30 -s 128x72 -an -f mp4 " + reencode_video_name
print("Invoking: " + ffcmd)
subprocess.call(ffcmd, shell=True, env=env)
print("Re-encoding Finished")

os.makedirs(output_dir, exist_ok=True)

video_name = inputvideo
video_start_num = int(options.start_num)

BLACK_COLOR = (0, 0, 0)
CUT_COLOR = (211.9, 236.5, 250.78)
CUT_STDDEV = (4.23, 4.31, 1.40)
COLOR_THR = int(options.threshold)
pre_cut = int(options.pre_cut)
sub_cut = int(options.sub_cut)


def color_diff(c0, c1):
    return ((c0[0] - c1[0])**2.0 + (c0[1] - c1[1])**2.0 + (c0[2] - c1[2])**2.0) ** 0.5


def is_black(color):
    return (COLOR_THR > color_diff(color, BLACK_COLOR))


def is_cut(color, stddev):
    return (COLOR_THR > color_diff(color, CUT_COLOR)) and (COLOR_THR > color_diff(stddev, CUT_STDDEV))


TIME_REPORT_INT = int(options.report)
FFMPEG_PARA = \
    ' -y -hide_banner -loglevel error -stats ' + \
    '  -c:v mpeg4 -b:v 24000k -r 30 -s 1280x720 -acodec aac -strict -2 -ac 2 -ab 256k -ar 44100 -f mp4 '

video = cv2.VideoCapture(reencode_video_name)
fps = video.get(cv2.CAP_PROP_FPS)
frame = 0

print(fps)

status = 0
# 0: Wait for next clip, want a cut-in
# 0->1
# 1: Cut in detected, want a black
# 1->2 mark black as ss
# 2: Record, want a cut-in, during 2, mark black as ut
# 2->0 save (ss, ut) to list
ss = 0
ut = 0
clip_list = []
nxt_report = 0
video_index = video_start_num

while(video.isOpened()):
    ret, rawImg = video.read()
    if not ret:
        break
    img = rawImg[0:52, :]
    time = frame / fps

    if (time >= nxt_report):
        if (status == 2):
            print("  %06.2f   |> CLIP_NUM  %02d" % (time, video_index))
        else:
            print("  %06.2f" % time)
        nxt_report = nxt_report + TIME_REPORT_INT

    color, stddev = cv2.meanStdDev(img)

    if (status == 0):
        if (is_cut(color, stddev)):
            status = 1
            print("%06.2f" % time, "CUT IN DETECTED, SEEKING BLACK FRAME.")
    if (status == 1):
        if (is_black(color)):
            ss = time + pre_cut/fps
            status = 2
            print("%06.2f" % time, "BLACK FRAME DETECTED SAVING CLIP.")
    if (status == 2):
        if (is_black(color)):
            ut = time - sub_cut/fps
        if (is_cut(color, stddev)):
            print("%06.2f" % time, "SAVING", ss, ut)
            clip_list.append((video_index, ss, ut-ss))
            video_index += 1
            status = 0
            print("%06.2f" % time, "RETURN TO SEEKING CUT IN.")

    frame += 1

    #cv2.imshow("img_crop", img)
    # cv2.waitKey(25)

print("%06.2f" % time, "FINISHED.")
video.release()

for clip in clip_list:
    video_index = clip[0]
    ss = clip[1]
    t = clip[2]
    print("-----------------------------------")
    print("PROCESSING", video_index, ss, t)
    print("-----------------------------------")
    os.makedirs(output_dir, exist_ok=True)
    cmd = "ffmpeg -ss " + str(ss) + " -t " + str(t) + " " + \
        ' -i ' + inputvideo + FFMPEG_PARA + \
        output_dir + ("%04d" % video_index) + ".mp4"
    print(cmd)
    subprocess.call(cmd, shell=True)
