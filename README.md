# Kirafan_AutoSub
## What is it?
A tool for replacing the Japanese text of Kirara Fantasia's story video

Here are some previews
* English Subtitled:  https://youtu.be/Z8BytfESak0
* Korean Subtitled:   https://youtu.be/_6IlXAgpsEs

Here is a simple tutorial
* https://www.youtube.com/watch?v=YVUm496x_K0

## How it works

### gensub.py
Analyse the original subtitle of Kirara Fantasia story
  - Crop binarized frames, ROI of subtitle area and track change on that area
  - Detect change the TextArea and NameTag
    - Analyse the same name of nmtg_%d.png, and bind them as the same string
  - Generate a timestamp of
    - TextArea fade-in, fade-out
    - Newline of subtitle
    - Carriage return
    - Inline Pause
  - Store information to autosub/videonam.krfss in json format
  - Capture the original subtitle (including name and text) as colored image
    - Store NameTag to autosub/videoname_img/nmtg_%04d.png
    - Store TextArea to autosub/videoname_img/text_%04d.png

### applysub.py
Apply the translated subtitle to the original video, it depends on
  - the timestamp file generated by gensub.py
  - the subtitle file generated edited by directly editing json file or using the web-based editing tools
  - a truetype font file in usr/font.ttf

## How to use it
### Dependence 
  Install these dependence below
  - python
    - Pillow
    - numpy
    - opencv2
  - ffmpeg (if you want to generate with audio track)
### Usage
  - Record a Kirara Fantasia Story video, make sure the resolution is 750 x 1334 (I recorded by iPhone 6s, iOS11)
  - Copy the video to an empty folder
  - Run the commands below, replace &lt;videoname&gt; by your actual video name
  > python gensub.py -i &lt;videoname&gt;
  
  - Edit the .krfss file by
    - Kirafan_Editor (recommanded)
      - Drag the .krfss into the gray box
      - Edit the name and text in right two columns
      - Click the Save box to save file
    - Directly editing json format
  > PS: for pink colored text, use a pair of $ to surround
      
  > Hmm, where would be a good place to start...\nKirara, you've read the $scriptures$, right?

  > Yes. \n$The goddess$ granted it to us, didn't she?
  
  > "The goddess" surrounded by a pair $ will be rendered in pink color
  
  - Ensure these is a font file in 'usr/font.ttf'
  - Run the commands below, replace &lt;videoname&gt; by your actual video name
  > python apply.py -i &lt;videoname&gt;
  
  - The output video will be videoname_out.m4v

### The web-based editing tool
  Preparing.
