# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import optparse


def concat(args):
    try:
        sys.setdefaultencoding('utf-8')
    except:
        pass

    parser = optparse.OptionParser(args)
    options, args = parser.parse_args()

    if (not len(args)):
        raise Exception("Missing input file.")
    arg0 = os.path.abspath(args[0])
    videolist = arg0
    if (not os.path.isfile(videolist)):
        videolist = arg0 + '/' + 'videolist.txt'
    if (not os.path.isfile(videolist)):
        raise Exception("Can not open " + videolist)
    filepwd = os.path.dirname(os.path.abspath(videolist))

    cmd = 'ffmpeg -y -f concat -safe 0 -i "' + \
        videolist + '" -c copy "' + filepwd + '/' + 'output.mp4"'
    print("Invoking " + cmd)
    subprocess.call(cmd, shell=False)


if __name__ == '__main__':
    concat(' '.join(sys.argv[1:]))
