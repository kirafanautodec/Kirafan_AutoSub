# -*- coding: utf-8 -*-
import numpy as np
import cv2
import os
import optparse
import glob

# Parse options
parser = optparse.OptionParser()
parser.add_option('-i', '--input',
    action="store", dest="input",
    help="input file of video file")
parser.add_option('-o', '--output',
    action="store", dest="output",
    help="output directory of generated files", default="html")

options, args = parser.parse_args()
if (not options.input):
    print("Missing argument for option 'i'.")
    exit(-1)
if (not os.path.isfile(options.input)):
    print("Video file do not exist" + options.input)
    exit(-1)
    
# output dir
filepwd = options.input + '_autosub'
print("Work directory: " + filepwd)

# open jpn files
jpndn = filepwd + '/' + 'img'
if (not os.path.isdir(jpndn)):
    print("Can not open dir: " + jpndn)
    exit(-1)
    
# get all nmtg files
nmtgfns = glob.glob(jpndn + '/' + 'nmtg*.png')

# judge if two nmtg_img are same
def is_same_name(img0, img1):
    kernel = np.ones((3,3), np.uint8)
    img0_dil_inv = cv2.bitwise_not(cv2.dilate(img0, kernel, iterations = 1))
    img1_dil_inv = cv2.bitwise_not(cv2.dilate(img1, kernel, iterations = 1))
    img_judge0 = cv2.bitwise_and(img0, img1_dil_inv)
    img_judge1 = cv2.bitwise_and(img1, img0_dil_inv)
    return 0 == np.sum(img_judge0) + np.sum(img_judge1)

# get_index in nmtg db
# if no same name in the db
# then append
def get_index(img1):
    for (i, img0) in enumerate(g_nmtg_img_db):
        if is_same_name(img0, img1):
            return i
    g_nmtg_img_db.append(img1)
    return len(g_nmtg_img_db) - 1
        
g_nmtg_img_db = []
# raw_nmtg_index -> db_index
nmtg_map = []

firstFlag = True
for nmtgfn in nmtgfns:
    img_nmtg = cv2.imread(nmtgfn, cv2.IMREAD_GRAYSCALE)
    if (firstFlag):
        firstFlag = False
        debug_nmtgs = img_nmtg
    else:
        debug_nmtgs = np.concatenate((debug_nmtgs, img_nmtg), axis=0)
    index = get_index(img_nmtg)
    nmtg_map.append(index)
    

# SHOW DEBUG IMAGE OF MAP 
import random
debug_num_diff = len(nmtgfns) - len(g_nmtg_img_db)
height_diff_div = int(40 * debug_num_diff / len(g_nmtg_img_db))
debug_blank_diff = np.full((height_diff_div, 400), 255, dtype=debug_nmtgs.dtype)
firstFlag = True
g_color = []
for i in g_nmtg_img_db:
    g_color.append((random.randint(40,230), random.randint(40,230), random.randint(40,230)))
    if (firstFlag):
        firstFlag = False
        debug_img_db = i
    else:
        debug_img_db = np.concatenate((debug_img_db, debug_blank_diff, i), axis=0)

debug_blank0 = np.full_like(debug_nmtgs, 255)
debug_blank0 = cv2.cvtColor(debug_blank0, cv2.COLOR_GRAY2BGR)
for (raw_index, db_index) in enumerate(nmtg_map):
    cv2.line(debug_blank0, \
             (5, 20 + raw_index * 40), (380, 20 + db_index * (40 + height_diff_div)), \
             g_color[db_index], \
             2, 8)

shape = (debug_nmtgs.shape[0] - debug_img_db.shape[0], debug_nmtgs.shape[1])
debug_blank1 = np.full(shape, 255, dtype=debug_nmtgs.dtype)
debug_img_db_e = np.concatenate((debug_img_db, debug_blank1), axis=0)

debug_nmtgs = cv2.cvtColor(debug_nmtgs, cv2.COLOR_GRAY2BGR)
debug_img_db_e = cv2.cvtColor(debug_img_db_e, cv2.COLOR_GRAY2BGR)
debug_map = np.concatenate((debug_nmtgs, debug_blank0, debug_img_db_e), axis=1)
resize_r = min(900.0 / debug_map.shape[0], 1)
debug_map = cv2.resize(debug_map, (int(debug_map.shape[1] * resize_r), int(debug_map.shape[0] * resize_r)))
cv2.imshow("db", debug_map)
cv2.waitKey(0)

# jsonp file
import json
jsonpfn = filepwd + '/' + os.path.basename(options.input) + '_subtitle.txt'
jsonpfp = open(jsonpfn, mode='w', encoding='utf-8')
json_nmtgs = [''] * len(nmtg_map)
json_trans = [''] * len(nmtg_map)
json_data = {"total": len(nmtg_map), "nmtgs": json_nmtgs, "trans": json_trans}
json_text = json.dumps(json_data, indent=2)
jsonpfp.write('subtitle(' + json_text + ')')

# save to html
html = '''
<!doctype html>
<html>
    <head>
        <meta charset="utf-8">
        <title>Download Sample</title>
        <style>
            div.item {
                margin-bottom: 20px;
                margin-top: 20px;
                padding-bottom: 10px;
                border-bottom: solid 3px #004;
                vertical-align:middle;
            }
            img.nmtg {
                width: 200px;
                border: solid 2px #966;
                padding: 2px;
                margin-right: 10px;
                vertical-align:middle;
            }
            img.text {
                width: 415px;
                padding: 2px;
                border: solid 2px #966;
                margin-right: 10px;
                vertical-align:middle;
            }
            input.nmtg {
                width: 200px;
                height: 20px;
                border: solid 2px #f00;
                padding: 2px;
                margin-right: 10px;
                font-size: 20px;
                vertical-align:middle;
                text-align: center;
            }
            textarea.tran {
                width: 415px;
                height: 60px;
                border: solid 2px #f00;
                padding: 2px;
                margin-right: 10px;
                font-size: 20px;
                vertical-align:middle;
            }
        </style>
    </head>
    <body style="width:calc(100% - 20px); text-align: center">
        <div style="display:inline-block; width: 1334px; text-align:center">'''

for (raw_index, db_index) in enumerate(nmtg_map):
    html += '''
            <div class="item">
                <img src="img/nmtg_%04d.png" class="nmtg">
                <img src="img/text_%04d.png" class="text">
                <input type="text" class="nmtg" id="nmtg_%d">
                <textarea rows="2" class="tran" id="tran_%d"></textarea>
            </div>''' % (raw_index, raw_index, raw_index, raw_index)
html += '''
            <a id="download_subtitle" href="#" download="''' + os.path.basename(options.input) + '_subtitle.txt' +'''" onclick="download_subtitle()">Download subtitle.txt</a>
        </div>
        <script type="text/javascript">
            window.onload = function() {
                g_krf_num = '''
html += str(len(nmtg_map))
html += '''
                g_krf_nmtg_map = {
'''

for (raw_index, db_index) in enumerate(nmtg_map):
    html += '%d: [' % raw_index
    firstFlag = True
    for (raw_jdex, db_jdex) in enumerate(nmtg_map):
        if (db_jdex == db_index and not raw_index == raw_jdex):
            html += ('%d' if firstFlag else ', %d' )% raw_jdex;
            firstFlag = False
    html += '],\n'

html += '''                }
                
                g_krf_nmtg = {}
                for (var i = 0; i < g_krf_num; ++i) {
                    g_krf_nmtg[i] = document.getElementById("nmtg_" + i);
                }
                g_krf_tran = {}
                for (var i = 0; i < g_krf_num; ++i) {
                    g_krf_tran[i] = document.getElementById("tran_" + i);
                }
                for (var i = 0; i < g_krf_num; ++i) {
                    g_krf_nmtg[i].addEventListener("change", function(){
                        var i = this.id.substring(5)
                        for (var j = 0; j < g_krf_nmtg_map[i].length; ++j) {
                            var maped_i = g_krf_nmtg_map[i][j]
                            g_krf_nmtg[maped_i].value = this.value
                        }
                    }, false);
                }
                var jsonpurl = "''' + os.path.basename(options.input) + '_subtitle.txt' + '''"
                var script = document.createElement("script")
                script.setAttribute("src", jsonpurl)
                document.getElementsByTagName("head")[0].appendChild(script)
                document.getElementsByTagName("head")[0].removeChild(script)
            }
            function download_subtitle() {
                var json = {total: g_krf_num, trans: [], nmtgs: []}
                for (var i = 0; i < g_krf_num; ++i) {
                    json.trans[i] = g_krf_tran[i].value
                    json.nmtgs[i] = g_krf_nmtg[i].value
                }
                var content = 'subtitle(' + JSON.stringify(json, null, 4) + ')'
                var content_r = content.replace("\\n", "\\r\\n").replace("\\r\\r", "\\r")
                console.log(content_r)
                var blob = new Blob([ content_r ], { "type" : "text/plain" });
                document.getElementById("download_subtitle").href = window.URL.createObjectURL(blob);
            }
            function subtitle(res) {
                if (g_krf_num != res.total) {
                    console.error("ERROR NUM")
                    return
                }
                for (var i = 0; i < g_krf_num; ++i) {
                    g_krf_nmtg[i].value = res.nmtgs[i]
                }
                for (var i = 0; i < g_krf_num; ++i) {
                    g_krf_tran[i].value = res.trans[i]
                }
            }
        </script>
    </body>
</html>'''

# html file
htmlfn = filepwd + '/' + 'html_gen.html'
htmlfp = open(htmlfn, mode='w', encoding='utf-8')
htmlfp.write(html)

