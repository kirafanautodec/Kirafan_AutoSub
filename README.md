# Kirafan_AutoSub
## What does it do
A tool for replacing the Japanese text of Kirara Fantasia's story video.

Here are some previews
* English Subtitled:  https://www.youtube.com/watch?v=02bVCTl3CUw
* Korean Subtitled:   https://www.youtube.com/watch?v=z7U6aLHBbV4

## How it works
### gensub.py
Detect the TextArea and NameTag and extract
* Timestamp (in frame) into a txt file.
* Japanese characters int TextArea into jpn/text_%04d.jpg file (OCR does not work perfectly.)
* Japanese characters int NameTag into jpn/nmtg_%04d.jpg file (OCR does not work perfectly.)
### applysub.py
Apply the translated subtitle to the original video
* Read the Timestamp file.
* Read translated NameTag file putted in 'sub/nmtgs.txt'.
* Read translated Script file putted in 'sub/trans.txt'.

#### Format of nmtgs.txt
Contains n lines, n equals the quantity of generated nmtg_%04d.jpg files.

Every lines is a translated name of corresponding Japanese named of nmtg_%04d.jpg.
#### Format of trans.txt
Contains n lines, n equals the quantity of generated text_%04d.jpg files.

Every lines is a translated script of corresponding Japanese text of text_%04d.jpg.

Do not input a newline evenif the Japanese text contains 2 lines. use '\n' instead.

For colored text, use a pair of $.

> Hmm, where would be a good place to start...\nKirara, you've read the $scriptures$, right?

> Yes. \n$The goddess$ granted it to us, didn't she?


## Usage
* python3 gensub.py -i <videofile_captured_by_Iphone_1334*750>
* create translated 'sub/trans.txt'. and 'sub/nmtgs.txt'. file.
* python3 applysub.py -i <videofile_captured_by_Iphone_1334*750>

## Dependence
python3, opencv2, Pillow, ffmpeg, a truetype font putted in 'usr/font.ttf'

## Comment
Please put your favourite font in 'usr/font.ttf'

