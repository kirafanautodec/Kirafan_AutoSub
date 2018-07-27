# -*- coding: utf-8 -*-
import subprocess
import os
import optparse

parser = optparse.OptionParser()
parser.add_option('-i', '--input',
    action="store", dest="input",
    help="input file of subtitle list")
parser.add_option('-o', '--output',
    action="store", dest="output",
    help="relative output filename of concated video clip", default="out.flv")
parser.add_option('--sub',
    action="store", dest="sub",
    help="relative directory of source videos", default="sub")
parser.add_option('--video',
    action="store", dest="video",
    help="relative directory of source videos", default="video")

options, args = parser.parse_args()
if (not options.input):
    print("Missing argument for option 'i'.")
    exit(-1)
if (not os.path.isfile(options.input)):
    print("Can not open subtitle file " + option.input)
    exit(-1)
    
filepwd = os.path.dirname(os.path.abspath(options.input))
print("Work directory: " + filepwd)
output = options.output
if(not os.path.isabs(output)):
    output = filepwd + '/' + output
    
sub = options.sub + '/'
if (not os.path.isabs(sub)):
    sub = filepwd + '/' + sub
video = options.video + '/'
if (not os.path.isabs(video)):
    video = filepwd + '/' + video

if (not os.path.isdir(video)):
    print("Video directory: " + video + " do not exists")
    exit(-1)
if (not os.path.isdir(sub)):
    print("Subtitle directory: " + sub + " do not exists")
    exit(-1)

videolist = os.listdir(video)
sublist = os.listdir(sub)
if (not len(videolist)):
    print("Video directory: " + video + " empty")
    exit(-1)
if (not len(sublist)):
    print("Video directory: " + video + " empty")
    exit(-1)
if (not int(videolist[-1][:4]) == len(videolist) or not int(videolist[0][:4]) == 1):
    print("Video directory: " + video + " number of videos error")
    exit(-1)
if (not int(sublist[-1][:4]) == len(sublist) or not int(sublist[0][:4]) == 1):
    print("Subtitle directory: " + video + " number of videos error")
    exit(-1)
if (not len(sublist) == len(videolist)):
    print("Numbers of Subtitle and Video not equal")
    exit(-1)

filelist = filepwd + '/ffmpeg_concat_list.temp.txt'
print("Outputing ffmpeg_concat_list for ffmpeg")
with open(filelist, mode='w', encoding='utf-8') as fp:
    op = False
    for i in range(0, len(sublist)):
        subf = options.sub + '/' + sublist[i]
        videof = options.video + '/' + videolist[i]
        fp.write("file '" + subf + "'\n")
        fp.write("file '" + videof + "'\n")
        if (not op):
            op = True
            fp.write("file '" + "op.flv" + "'\n")
    fp.write("file '" + "ed.flv" + "'\n")

print("Concating")
import subprocess
cmd = "ffmpeg -y -f concat -safe 0 -i " + filelist + " -c copy " + output
print (cmd)
subprocess.call(cmd, shell=False)
#os.remove(filelist)