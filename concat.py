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
    videolist = arg0
    if (not os.path.isfile(videolist)):
        videolist = arg0 + '/' + 'videolist.txt'
    if (not os.path.isfile(videolist)):
        raise Exception("Can not open " + videolist)
    filepwd = os.path.dirname(os.path.abspath(videolist))

    cmd = 'ffmpeg -y -f concat -safe 0 -i "' + \
        videolist + '" -c copy "' + filepwd + '/' + 'output.mp4"'
    print("Invoking " + cmd)
    subprocess.call(cmd, shell=True, env=env)


if __name__ == '__main__':
    concat(' '.join(sys.argv[1:]))
