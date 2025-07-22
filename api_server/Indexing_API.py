from flask import Flask, request, send_file, jsonify
import xml.etree.ElementTree as ET
import pandas as pd
import subprocess
import os
import stat

def read_cntl_inp_xml (path):
    # XMLファイルを読み込む
    tree = ET.parse(path)  # ファイル名を適宜変更
    root = tree.getroot()

    # 各要素の取得
    control_param = root.find('.//ControlParamFile')
    control_param_file = control_param.text.strip() if control_param is not None else None

    peakdata_file = root.find('.//PeakDataFile')
    peakdata_file_name = peakdata_file.text.strip() if peakdata_file is not None else None

    outfile = root.find('.//OutputFile')
    outfile_name = outfile.text.strip() if outfile is not None else None
    return control_param_file, peakdata_file_name, outfile_name

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(CURRENT_DIR)
PATH_cntl = os.path.join (CURRENT_DIR, 'cntl.inp.xml')
PATH_param, PATH_peak, PATH_out =  read_cntl_inp_xml (PATH_cntl)

FOLDER_out = os.path.dirname (PATH_out)
if FOLDER_out is not None:
    os.makedirs (FOLDER_out, exist_ok = True)
PATH_exe = os.path.join (CURRENT_DIR, 'Conograph')
PATH_log = os.path.join (CURRENT_DIR, 'LOG_CONOGRAPH.txt')

app = Flask(__name__)

@app.route("/run_cpp", methods = ["POST"])
def run_cpp_with_cntl():
    if os.path.exists (PATH_param): os.remove (PATH_param)
    if os.path.exists (PATH_peak): os.remove (PATH_peak)
    if os.path.exists (PATH_out): os.remove (PATH_out)
    if os.path.exists (PATH_log): os.remove (PATH_log)

    pathDict = {'xml' : PATH_param, 'txt' : PATH_peak,
                'histogramIgor' : PATH_peak, 'histogramIgor_pk' : PATH_peak}
    for key in request.files:
        f = request.files[key]
        fname = f.name
        suffix = fname.split('.')[-1]
        path = pathDict[suffix]
        path = os.path.join (CURRENT_DIR, path)
        f.save(path)

    if not os.access (PATH_exe, os.X_OK):
       os.chmod(PATH_exe, os.stat (PATH_exe).st_mode | stat.S_IEXEC)
    result = subprocess.run([PATH_exe], input = 'quit\n',
                    capture_output=True, text=True)
    #result = subprocess.run(
    #                ['.\Conograph.exe'],  # 実行するexeのパス
    #                input = 'quit\n',                  # 入力として quit を渡す
    #                text = True,                       # strとして渡す（バイナリでなく）
    #                capture_output = True)
    
    if os.path.exists (PATH_out):
        return send_file(PATH_out, as_attachment = True), 200
    else:
        return jsonify({"error": "出力ファイルがありません"}), 500

@app.route ('/log_file', methods = ['POST'])
def log_file ():
    if os.path.exists (PATH_log):
        return send_file (PATH_log, as_attachment = True), 200
    else:
        return jsonify ({'error' : '送信ファイルがありません'}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port = 8100, debug = False)