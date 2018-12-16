# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
import subprocess
import os
import sys
import optparse
import codecs


def gensub(args):
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

    voidwav = python_dir + "/usr/Void.wav"
    if (not os.path.isfile(voidwav)):
        voidwav = highPath + "/usr/Void.wav"
    if (not os.path.isfile(voidwav)):
        print("Can not load Void.wav")
    subtemp = "subtemp.png"

    cnfontf = python_dir + "/cnfont.ttf"
    if (not os.path.isfile(cnfontf)):
        cnfontf = python_dir + "/usr/cnfont.ttf"
    if (not os.path.isfile(cnfontf)):
        cnfontf = highPath + "/usr/cnfont.ttf"

    parser = optparse.OptionParser(args)
    parser.add_option('-d', '--duration',
                      action="store", dest="duration",
                      help="duration of every title subclip", default=3)
    parser.add_option('--font',
                      action="store", dest="font",
                      help="path to ttf fontfile", default=cnfontf)
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
    if (not len(args)):
        raise Exception("Missing input file.")
    arg0 = os.path.abspath(args[0])
    inputfile = arg0
    if (not os.path.isfile(inputfile)):
        inputfile = arg0 + '/' + 'title.txt'
    if (not os.path.isfile(inputfile)):
        raise Exception("Can not open " + inputfile)

    filepwd = os.path.dirname(os.path.abspath(inputfile))
    print("Work directory: " + filepwd)
    output = filepwd + '/'
    outputfile = output + 'videolist.txt'

    duration = int(options.duration)
    if (duration > 15):
        duration = 15

    FFMPEG_PARA = ' -y -hide_banner -loglevel error ' + \
        ' -vcodec mpeg4 -preset slow ' + \
        ' -b:v 24000k -r 30 -s 1280x720 -t ' + str(duration) + \
        ' -acodec aac -strict -2 -ac 2 -ab 256k -ar 44100 -f mp4 '

    print("Opening " + inputfile)
    print("Writing " + outputfile)
    fp = open(inputfile, mode='r', encoding='utf-8')
    ofp = open(outputfile, mode='w')
    text = fp.read()
    if (not text):
        raise Exception("Text is empty")
    if (text[0].encode('utf-8') == codecs.BOM_UTF8):
        text = text[1:]
    video_index = int(options.start_num)
    for raw_title in text.split('\n'):
        title = raw_title.replace('\\n', '\n')
        W, H = (int(options.width), int(options.height))
        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(options.font, int(options.fontsize))
        w, h = draw.textsize(title, font=font)
        draw.text(((W-w)/2, int(options.positionY)), title, fill=(int(options.colorR),
                                                                  int(options.colorG), int(options.colorB)), font=font)
        os.makedirs(output, exist_ok=True)
        img.save(subtemp, "PNG")

        cmd = 'ffmpeg -loop 1 -i "' + subtemp + '" -i "' + voidwav + '"' + \
            FFMPEG_PARA + '"' + output + \
            ("%04d" % video_index) + '.title.mp4"'
        print(video_index, title)
        print("Invoking: " + cmd)
        subprocess.call(cmd, shell=True)

        titlefilename = "%04d.title.mp4" % video_index
        autosubedfilename = "%04d.mp4.autosubed.mp4" % video_index
        ofp.write("file " + "'" + titlefilename + "'\n")
        ofp.write("file " + "'" + autosubedfilename + "'\n")

        video_index += 1

        os.remove(subtemp)
    fp.close()
    ofp.close()


if __name__ == '__main__':
    gensub(' '.join(sys.argv[1:]))
