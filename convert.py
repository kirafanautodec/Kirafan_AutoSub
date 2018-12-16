# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import optparse


def convert(args):
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

    parser = optparse.OptionParser(args)
    options, args = parser.parse_args()
    if (not len(args)):
        raise Exception("Missing input file.")
    arg0 = os.path.abspath(args[0])
    inputvideo = arg0
    if (not os.path.isfile(inputvideo)):
        raise Exception("Can not open " + inputvideo)

    FFMPEG_PARA = \
        ' -y -hide_banner -loglevel error -stats ' + \
        ' -c:v mpeg4 -preset slow -b:v 24000k -r 30 -s 1280x720 -acodec aac -strict -2 -ac 2 -ab 256k -ar 44100 -f mp4 '

    outputfile = inputvideo + ".cvt.mp4"

    print("Convert to " + outputfile)
    cmd = "ffmpeg" + ' -i "' + inputvideo + '"' + FFMPEG_PARA + \
        '"' + outputfile + '"'
    print("Invoking " + cmd)
    subprocess.call(cmd, shell=True)


if __name__ == '__main__':
    convert(' '.join(sys.argv[1:]))
