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
nmtg_blank_f = python_dir + "/usr/nmtg.png"

parser = optparse.OptionParser()
parser.add_option('-i', '--input',
    action="store", dest="input",
    help="input file of video file")
parser.add_option('--gray_threshold',
    action="store", dest="gray_threshold",
    help="gray_threshold of binarization", default=160)
parser.add_option('--blank_extra_pre',
    action="store", dest="blank_pre",
    help="inpaint blank before textarea completely reach its position", default=3)
parser.add_option('--nmtg_extra_pre',
    action="store", dest="nmtg_pre",
    help="inpaint nmtg before textarea completely reach its position", default=0)
parser.add_option('--blank_extra_sub',
    action="store", dest="blank_sub",
    help="inpaint blank after textarea start to disappear", default=0)
parser.add_option('--typed_speed',
    action="store", dest="typed_speed",
    help="typed effect(text rolling) speed, char per s", default=5)
parser.add_option('--fontsize',
    action="store", dest="fontsize",
    help="font size of translated", default=36)
parser.add_option('--ffmpeg_encoder',
    action="store", dest="ffmpeg_encoder",
    help="ffmpeg encoder, default = libx264, use h264_nvenc if available", default="libx264")

options, args = parser.parse_args()
if (not options.input):
    print("Missing argument for option 'i'.")
    exit(-1)
if (not os.path.isfile(options.input)):
    print("Can not open video file " + option.input)
    exit(-1)
    
# output dir
basename = os.path.basename(options.input)
dirname = os.path.dirname(options.input)
script_dir = dirname + ('/' if dirname else '') + 'autosub'

script_fn = script_dir + '/' + basename + '.krfss'
print("Script file: " + script_fn)
if (not os.path.isfile(script_fn)):
    print("Can not open video file " + script_fn)
    exit(-1)

frame_cmds = {}
frame_subindex = {}
frame_haveblank = {}
frame_havenmtg = {}
frame_index_temp = 0
frame_index_temp1 = 0

# read script
import json
with open(script_fn, mode='r', encoding='utf-8') as fp:
    text = fp.read()
    if (text[0].encode('utf-8') == codecs.BOM_UTF8):
        text = text[1:]
    script = json.loads(text)
    

for command in script["timestamp"]:
    frame = int(command["at"])
    action = command["action"]
    if (action == 'S' or action == 'E' or action == 'C'):
        frame_cmds[frame] = action
    if (action == 'S'):
        subindex = int(command["sub"])
        frame_subindex[frame] = subindex
    if (action == 'T'):
        for i in range(frame_index_temp, frame - int(options.blank_pre)):
            frame_haveblank[i] = False
        frame_index_temp = frame - int(options.blank_pre)
        for i in range(frame_index_temp1, frame - int(options.nmtg_pre)):
            frame_havenmtg[i] = False
        frame_index_temp1 = frame - int(options.nmtg_pre)
    if (action == 'X'):
        for i in range(frame_index_temp, frame + int(options.blank_sub)):
            frame_haveblank[i] = True
        frame_index_temp = frame + int(options.blank_sub)
        for i in range(frame_index_temp1, frame):
            frame_havenmtg[i] = True
        frame_index_temp1 = frame
    if (action == 'O'):
        for i in range(frame_index_temp, frame + 1):
            frame_haveblank[i] = False
        frame_index_temp = frame
        for i in range(frame_index_temp1, frame + 1):
            frame_havenmtg[i] = False
        frame_index_temp1 = frame

print (script["trans"])
print (script["nmtgs"])

video_name = options.input
video = cv2.VideoCapture(video_name)
fps = video.get(cv2.CAP_PROP_FPS)
# Iphone's video is rotated
width = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
height = video.get(cv2.CAP_PROP_FRAME_WIDTH)
# temp output without audio track
out_name = options.input + '_out.m4v'
fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
out_video = cv2.VideoWriter(out_name, int(fourcc), fps, (int(width), int(height)))

frame = 0
font_text = ImageFont.truetype(fontf, int(options.fontsize))
img_nmtg_blank = cv2.imread(nmtg_blank_f)

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

    if (frame in frame_cmds):
        cmd = frame_cmds[frame]
        if (cmd == 'C'):
            str_todraw = ''
            print(frame, "C")
        if (cmd == 'S'):
            last_typed_start = frame
            index_sub = frame_subindex[frame]
            str_typed_cache = script["trans"][index_sub].replace('\\n', '\n').replace('\\"', '"')
            print(frame, "S")
            print(str_typed_cache)
        if (cmd == 'E'):
            str_todraw += str_typed_cache
            str_typed_cache = ''
            print(frame, "E")
            print(str_todraw)
            
    is_blank = frame_haveblank[frame]
    is_nmtg = frame_havenmtg[frame]

    if (is_blank):
        # binarization
        img_gray = cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY)
        retval, img_bin = cv2.threshold(img_gray, int(options.gray_threshold), 255, cv2.THRESH_BINARY)
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

    nmtg = script["nmtgs"][script["nmtg_map"][index_sub]]
    if (is_nmtg and len(nmtg)):
        img_inpaint[5:55, 5:405] = img_nmtg_blank
        
    if (is_blank):
        img_pil = Image.fromarray(img_inpaint)
        draw = ImageDraw.Draw(img_pil)
        str_typed_render = str_typed_cache[:min(len(str_typed_cache), int(float(options.typed_speed) * (frame - last_typed_start + 1)))]
        str_splited = (str_todraw + str_typed_render).split('\n')
        font_w, font_h = draw.textsize("LIPFgYTjyXSq|^#%", font = font_text)
        for (lineindex, text_line) in enumerate(str_splited):
            draw_x = 170
            draw_y0 = 162 if (lineindex > 0) else 105
            for (spanindex, text_span) in enumerate(text_line.split('$')):
                color = (60, 66, 111) if (spanindex % 2 == 0) else (150, 106, 255)
                span_w, span_h = draw.textsize(text_span, font = font_text)
                draw_y = draw_y0 - font_h / 2
                draw.text((draw_x, draw_y), text_span, fill = color, font = font_text)
                draw_x += span_w
        
    if (is_nmtg and len(nmtg)):
        img_draw_nmtg = Image.new("RGB", (400, 50))
        draw_nmtg = ImageDraw.Draw(img_draw_nmtg)
        w_nmtg, h_nmtg = draw.textsize(nmtg, font=font_text)
        draw.text((207 - w_nmtg / 2, 30 - font_h / 2), nmtg, fill = (255,255,255), font = font_text)

    if (is_blank):
        img_drawed = np.array(img_pil)
        img_rot[520:740, 80:1180] = img_drawed

    cv2.imshow("img_merged", img_rot)
    cv2.waitKey(1)
    out_video.write(img_rot)

video.release()
out_video.release()

exit(0)
ffcmd = "ffmpeg -y -vn -i " + video_name + " -acodec copy " + video_name + ".aac"
print (ffcmd)
subprocess.call(ffcmd, shell=True)
ffcmd = "ffmpeg -i " + out_name + " -i " + video_name + ".aac " + " -vcodec " + options.ffmpeg_encoder + " -preset slow -profile:v high -level:v 4.1 -pix_fmt yuv420p -b:v 1780k -r 30 -acodec aac -strict -2 -ac 2 -ab 192k -ar 44100 -f flv " + video_name + ".out.flv"
print (ffcmd)
subprocess.call(ffcmd, shell=True)
