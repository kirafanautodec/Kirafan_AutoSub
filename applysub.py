# -*- coding: utf-8 -*-
import os
import optparse
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import codecs
import subprocess

python_dir = os.path.dirname(os.path.abspath(__file__))
fontf = python_dir + "/usr/font.ttf"
nmtgf = python_dir + "/usr/nmtg.png"

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
    print("Can not open subtitle file " + option.input)
    exit(-1)
    
# input dir
filepwd = os.path.dirname(os.path.abspath(options.input))
print("Work directory: " + filepwd)
    
frame_cmds = {}
# read timestampfile
timestampfn = filepwd + '/sub/timestamp.txt'
with open(timestampfn, mode='r', encoding='utf-8') as fp:
    text = fp.read()
    if (text[0].encode('utf-8') == codecs.BOM_UTF8):
        text = text[1:]
    for line in text.split('\n'):
        cmds = line.split(' ')
        if (len(cmds) < 2):
            break
        frame = int(cmds[0])
        action = cmds[1]
        if (action == 'S' or action == 'E' or action == 'C'):
            frame_cmds[frame] = action
# read translation the main text
trans = []
transfn = filepwd + '/sub/trans.txt'
with open(transfn, mode='r', encoding='utf-8') as fp:
    text = fp.read()
    if (text[0].encode('utf-8') == codecs.BOM_UTF8):
        text = text[1:]
    for line in text.split('\n'):
        t = line.replace('\\n','\n')
        trans.append(t)

# read translation name
nmtgs = []
nmtgsfn = filepwd + '/sub/nmtgs.txt'
with open(nmtgsfn, mode='r', encoding='utf-8') as fp:
    text = fp.read()
    if (text[0].encode('utf-8') == codecs.BOM_UTF8):
        text = text[1:]
    for line in text.split('\n'):
        nmtgs.append(line)

print (trans)
print (nmtgs)

# COLOR DEFINITION
BLANK_COLOR_MAX = (250, 256, 256)
BLANK_COLOR_MIN = (190, 190, 210)
NMTAG_COLOR_MAX = ( 84, 113, 155)
NMTAG_COLOR_MIN = ( 34,  63, 125)

def is_blank_p(p):
    return \
            (BLANK_COLOR_MAX[0] > p[0] > BLANK_COLOR_MIN[0]) and \
            (BLANK_COLOR_MAX[1] > p[1] > BLANK_COLOR_MIN[1]) and \
            (BLANK_COLOR_MAX[2] > p[2] > BLANK_COLOR_MIN[2])
def is_nmtag_p(p):
    return \
            (NMTAG_COLOR_MAX[0] > p[0] > NMTAG_COLOR_MIN[0]) and \
            (NMTAG_COLOR_MAX[1] > p[1] > NMTAG_COLOR_MIN[1]) and \
            (NMTAG_COLOR_MAX[2] > p[2] > NMTAG_COLOR_MIN[2])
            
def is_blank_func(im0, im1, im2):
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

def is_nmtag_func(im2):
    i2 = np.asarray(im2)
    for ln in i2:
        for p in ln:
            if not is_nmtag_p(p):
                return False
    return True
    
video_name = options.input
video = cv2.VideoCapture(video_name)
fps = video.get(cv2.CAP_PROP_FPS)
# Iphone's video is rotated
width = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
height = video.get(cv2.CAP_PROP_FRAME_WIDTH)
# temp output without audio track
out_name = filepwd + '/' + 'out.m4v'
fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
out_video = cv2.VideoWriter(out_name, int(fourcc), fps, (int(width), int(height)))

frame = 0
font_text = ImageFont.truetype(fontf, 36)
img_nmtg_blank = cv2.imread(nmtgf)

# static string
str_todraw = ''
# a 'typed' effect
str_typed_cache = ''
str_typed_render = ''
last_typed_start = 0
index_sub = -1
while(video.isOpened()):
    ret, img = video.read()
    if not ret:
        break
    time = frame / fps
    frame += 1
    
# Iphone's video is rotated
    img_rot = np.rot90(img)
    # ROI of TextArea and NameTag
    img_crop = img_rot[520:740, 80:1180]

    # Judge ROI of TextArea
    img_judge0 = img_crop[78:80, 130:1000]
    img_judge1 = img_crop[183:185, 130:1000]
    # Judge ROI of NameTag
    img_judge2 = img_crop[50:52, 150:400]
    # TextArea exist?
    is_blank = is_blank_func(img_judge0, img_judge1, img_judge2)
    # NameTag exist?
    is_nmtag = is_nmtag_func(img_judge2)

    # binarization
    img_gray = cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY)
    retval, img_bin = cv2.threshold(img_gray, int(options.gray_threshold), 255, cv2.THRESH_BINARY)

    if (frame in frame_cmds):
        cmd = frame_cmds[frame]
        if (cmd == 'C'):
            str_todraw = ''
            print(frame, "C")
        if (cmd == 'S'):
            last_typed_start = frame
            index_sub += 1
            str_typed_cache = trans[index_sub]
            print(frame, "S")
            print(str_typed_cache)
        if (cmd == 'E'):
            str_todraw += str_typed_cache
            str_typed_cache = ''
            print(frame, "E")
            print(str_todraw)

    if (is_blank):
        img_mask = cv2.bitwise_not(img_bin)
        img_mask[:88, :] = 0
        img_mask[185:,:] = 0
        img_mask[:, :165] = 0
        img_mask[:, 1000:] = 0
        neiborhood8 = np.array([[1, 1, 1],
                        [1, 1, 1],
                        [1, 1, 1]],
                        np.uint8)
        img_mask = cv2.dilate(img_mask, neiborhood8, iterations=2)
        # Inpaint to repair?
        img_inpaint = cv2.inpaint(img_crop, img_mask, 3, cv2.INPAINT_TELEA)
    else:
        img_inpaint = img_crop

    if (is_blank and len(nmtgs[index_sub])):
        img_inpaint[5:55, 5:405] = img_nmtg_blank

    img_pil = Image.fromarray(img_inpaint)
    draw = ImageDraw.Draw(img_pil)
    str_typed_render = str_typed_cache[:min(len(str_typed_cache), int(10*(frame - last_typed_start + 1)))]
    str_splited = (str_todraw + str_typed_render).split('\n')
    if (len(str_splited) == 1):
        draw.text((170,  87), str_splited[0], font = font_text, fill = (60,66,111))
    elif (len(str_splited) == 2):
        draw.text((170,  87), str_splited[0], font = font_text, fill = (60,66,111))
        draw.text((170, 144), str_splited[1], font = font_text, fill = (60,66,111))
    if (is_blank and len(nmtgs[index_sub])):
        img_draw_nmtg = Image.new("RGB", (400, 50))
        draw_nmtg = ImageDraw.Draw(img_draw_nmtg)
        w_nmtg, h_nmtg = draw.textsize(nmtgs[index_sub], font=font_text)
        draw.text((207-w_nmtg/2, 30-h_nmtg/2), nmtgs[index_sub], fill = (255,255,255), font = font_text)

    img_drawed = np.array(img_pil)
    img_rot[520:740, 80:1180] = img_drawed
    cv2.imshow("img_merged", img_rot)
    cv2.waitKey(1)
    out_video.write(img_rot)

video.release()
out_video.release()

ffcmd = "ffmpeg -y -vn -i " + video_name + " -acodec copy " + video_name + ".aac"
print (ffcmd)
subprocess.call(ffcmd, shell=False)
ffcmd = "ffmpeg -i " + out_name + " -i " + video_name + ".aac " + " -vcodec h264_nvenc -preset slow -profile:v high -level:v 4.1 -pix_fmt yuv420p -b:v 1780k -r 30 -acodec aac -strict -2 -ac 2 -ab 192k -ar 44100 -f flv -t 30 " + video_name + ".out.flv"
print (ffcmd)
subprocess.call(ffcmd, shell=False)
