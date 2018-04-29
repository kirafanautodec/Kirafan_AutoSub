# Kirafan_AutoSub
## What does it do
A tool for replacing the Japanese text of Kirara Fantasia's story video.

Here is a preview https://www.youtube.com/watch?v=RECYWkwCW5E
## How it works
### gensub.py
Detect the TextArea and NameTag and extract
* Timestamp (in frame) into a txt file.
* Japanese characters int TextArea into text_%04d.jpg file (OCR does not work perfectly.)
* Japanese characters int NameTag into nmtg_%04d.jpg file (OCR does not work perfectly.)
### applysub.py
Apply the translated subtitle to the original video
* Read the Timestamp file.
* Read translated NameTag file putted in 'sub/nmtgs.txt'.
* Read translated Script file putted in 'sub/trans.txt'.

#### Format of nmtgs.txt
Contains n lines, n equals the quantity of generated nmtg_%04d.jpg files.
#### Format of trans.txt
Contains n lines, n equals the quantity of generated text_%04d.jpg files.
'\n' for a newline inside the script.

## Usage
* python3 gensub.py -i <videofile_captured_by_Iphone_1334*750>
* create translated 'sub/trans.txt'. and 'sub/nmtgs.txt'. file.
* python3 applysub.py -i <videofile_captured_by_Iphone_1334*750>

## Dependence
python3, opencv2, Pillow, ffmpeg

## Comment
Please put your favourite font in 'usr/font.ttf'

I used h264_nvenc, if your PC do not support that please change ffmpeg parameters in applysub.py

