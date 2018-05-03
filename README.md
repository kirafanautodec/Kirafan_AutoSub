# Kirafan_AutoSub
## What is it?
A tool for replacing the Japanese text of Kirara Fantasia's story video

Sample ouput:(generated by ver2.0)
* English Subtitled:

  [![IMAGE ALT TEXT](http://img.youtube.com/vi/Z8BytfESak0/0.jpg)](https://www.youtube.com/embed/Z8BytfESak0 "CameraMaster")
* Korean Subtitled:   

  [![IMAGE ALT TEXT](http://img.youtube.com/vi/_6IlXAgpsEs/0.jpg)](https://www.youtube.com/embed/_6IlXAgpsEs "CameraMaster")

Here is a simple tutorial
* [![IMAGE ALT TEXT](http://img.youtube.com/vi/Ocl9qwsXkFo/0.jpg)](https://www.youtube.com/embed/Ocl9qwsXkFo "CameraMaster")

## Build
### on Windows (and you do not want to install python)
  Use pre-built binaries:
  - analyse_video.exe:    https://drive.google.com/open?id=1Zhec8rAaMLsWQNuVjrBHpF2NLKHUDUx2
  - patch_subtitle.exe:   https://drive.google.com/open?id=1eBjmstyS_kd7qo9FDL8QxsKQoAAMW1r4
  - all the file(analyse_video.exe v5.0.0 + patch_subtitle.exe v5.0.0 + Krfss_Editor v3.0.1): https://drive.google.com/open?id=1uuZojwzCLgPr2PZn8OrjQnHPkNXvgSgT
### on Linux or Mac, (or you want to use it in terminal even on Window)
#### Dependence 
  Install these dependence below
  - python (version 3)
  - python libraries
    - pillow
    - numpy
    - opencv-python
  - ffmpeg
  
  and make sure to include their directory in $PATH
  
## Usage
  - Record a Kirara Fantasia Story video
  - Copy the video to an empty folder
  - Run analyse_video
    - on \*Nix, Run the commands below, replace &lt;videoname&gt; by your actual video name
    > python analyse_video.py -i &lt;videoname&gt;
    - on Windows, drag video file into analyse_video.exe
  
  - Edit the generated autosub/&lt;videoname&gt.krfss file by
    - Krfss_Editor (recommanded) ( https://github.com/kirafanautodec/Krfss_Editor , pre-built binaries on Windows: https://drive.google.com/open?id=1XDZ-TluLkJg7T0ClgSVo_1Ohd8UClVz2)
      - Drag the .krfss file into the gray box
      - Edit the name and text in right two columns
      - Click the Save box to save file
    - Or directly editing json format
  > PS: for pink colored text, use a pair of $ to surround
      
  > Hmm, where would be a good place to start...\nKirara, you've read the $scriptures$, right?

  > Yes. \n$The goddess$ granted it to us, didn't she?
  
  > "The goddess" surrounded by a pair $ will be rendered in pink color
  
  - Ensure the font file 'usr/font.ttf' is suitable for the translated language
    - This repo's default one is 'Source Sans Pro', which only supports ASCII characters
    - You should replace 'usr/font.ttf' if you want to render CJK characters
    - on Windows, put a font.ttf in the same directory of patch_subtitle.exe
  - Run patch_subtitle
    - on, \*nix, Run the commands below, replace &lt;videoname&gt; by your actual video name
    > python patch_subtitle.py -i &lt;videoname&gt;
    - on Windows, drag video file into patch_subtitle.exe
  
  - The output video will be &lt;videoname&gt;_autosubed.flv

### The web-based editing tool
  refer https://github.com/kirafanautodec/Krfss_Editor
  
  pre-built binaries on Windows: https://drive.google.com/open?id=1XDZ-TluLkJg7T0ClgSVo_1Ohd8UClVz2)

## How it works

### analyse_video.py
Firstly, re-encode the recorded video into 1280x720 30fps mpg format
  - Since most mobile devices record video in VFR mode, causing the difference between audio desync after output
  
Then, Analyse the original subtitle of Kirara Fantasia story
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

### patch_subtitle.py
Firstly, apply the translated subtitle to the re-encoded video, it depends on
  - the .krfss file generated by gensub.py and edited by directly editing json file or using the web-based editing tools
  - a truetype font file in usr/font.ttf
  
Then, call ffmpeg to combine the output video and the audio


