# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
import subprocess
import os
import optparse
import codecs

cwd = os.path.dirname(os.path.abspath(__file__))
voidwav = cwd + "/usr/Void.wav"
subtemp = cwd + "/subtemp.png"

parser = optparse.OptionParser()
parser.add_option('-i', '--input',
    action="store", dest="input",
    help="input file of subtitle list")
parser.add_option('-o', '--output',
    action="store", dest="output",
    help="output directory of generated title subclip", default="sub")
parser.add_option('-d', '--duration',
    action="store", dest="duration",
    help="duration of every title subclip", default=3)
parser.add_option('--font',
    action="store", dest="font",
    help="path to ttf fontfile", default=cwd + "/usr/font.ttf")
parser.add_option('--fontsize',
    action="store", dest="fontsize",
    help="fontsize", default=64)
parser.add_option('--colorR',
    action="store", dest="colorR",
    help="color red", default=255)
parser.add_option('--colorG',
    action="store", dest="colorG",
    help="color green", default=236)
parser.add_option('--colorB',
    action="store", dest="colorB",
    help="color blue", default=211)
parser.add_option('--positionY',
    action="store", dest="positionY",
    help="title position in Y axis", default=480)
parser.add_option('--start_num',
    action="store", dest="start_num",
    help="start num of sub index", default=1)
parser.add_option('--width',
    action="store", dest="width",
    help="width of video", default=1280)
parser.add_option('--height',
    action="store", dest="height",
    help="height of video", default=720)

options, args = parser.parse_args()
if (not options.input):
    print("Missing argument for option 'i'.")
    exit(-1)
if (not os.path.isfile(options.input)):
    print("Can not open subtitle file " + option.input)
    exit(-1)
    
filepwd = os.path.dirname(os.path.abspath(options.input))
print("Work directory: " + filepwd)
output = options.output + '/'
if(not os.path.isabs(output)):
    output = filepwd + '/' + output

duration = int(options.duration)
if (duration > 15):
    duration = 15

FFMPEG_PARA = \
    ' -y -hide_banner -loglevel error ' + \
    ' -vcodec h264_nvenc -preset slow ' + \
    ' -profile:v high -level:v 4.1 -pix_fmt yuv420p -t ' + str(duration) + \
    ' -b:v 1780k -r 30 ' + \
    ' -acodec aac -strict -2 -ac 2 -ab 192k -ar 44100 -f flv '

with open(options.input, mode='r', encoding='utf-8') as fp:
    text = fp.read()
    if (text[0].encode('utf-8') == codecs.BOM_UTF8):
        text = text[1:]
    video_index = int(options.start_num)
    for raw_title in text.split('\n'):
        title = raw_title.replace('\\n','\n')
        W, H = (int(options.width), int(options.height))
        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(options.font, int(options.fontsize))
        w, h = draw.textsize(title, font=font)
        draw.text(((W-w)/2, int(options.positionY)), title, fill=(int(options.colorR), int(options.colorG), int(options.colorB)), font=font)
        os.makedirs(output, exist_ok=True)
        img.save(subtemp, "PNG")

        cmd = "ffmpeg -loop 1 -i " + subtemp + " -i " + voidwav + FFMPEG_PARA + output + ("%04d"%video_index) + ".flv"
        print (video_index, title)
        subprocess.call(cmd, shell=True)
        video_index += 1
    
    os.remove(subtemp)