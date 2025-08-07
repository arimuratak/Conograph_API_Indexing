from flask import Flask, request, send_file, jsonify
import xml.etree.ElementTree as ET
import subprocess
import os
import stat
import glob
import shutil
import threading
lock = threading.Lock()

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
PATH_zip = os.path.join (CURRENT_DIR, 'archive.zip')
PATH_output = os.path.join (CURRENT_DIR, 'output')

FOLDER_out = os.path.dirname (PATH_out)
if FOLDER_out is not None:
    os.makedirs (FOLDER_out, exist_ok = True)

if os.name == 'nt':
    PATH_exe = '.\Conograph.exe'
else:
    PATH_exe = os.path.join (CURRENT_DIR, 'Conograph')
    if not os.access (PATH_exe, os.X_OK):
            os.chmod(PATH_exe, os.stat (PATH_exe).st_mode | stat.S_IEXEC)

PATH_log = os.path.join (CURRENT_DIR, 'LOG_CONOGRAPH.txt')


app = Flask(__name__)

def exec_run_cmd (cmd):
    #if os.name != 'nt':
    #    if not os.access (PATH_exe, os.X_OK):
    #        os.chmod(PATH_exe, os.stat (PATH_exe).st_mode | stat.S_IEXEC)
     
    result = subprocess.run([PATH_exe],
                    input = cmd,
                capture_output = True, text = True)    

    return result

def clean_output_folder ():
    paths = glob.glob ('output/*.*')
    paths = [path for path in paths if 'index.xml' not in path]
    if len (paths) > 0:
        for path in paths:
            os.remove (path)

def search_file (suffix = 'xml',
        matching_pattern = 'sample_lattice('):
    paths = glob.glob ('output/*.' + suffix)
    paths = [path for path in paths if matching_pattern in path]
    if len (paths) > 0: return paths[0]
    else: return None

def send_file_with_name (path):
    response = send_file (path, as_attachment = True)
    response.headers ['file_name'] = path
    return response

@app.route("/run_cpp", methods = ["POST"])
def run_cpp_with_cntl():
    if os.path.exists (PATH_param): os.remove (PATH_param)
    if os.path.exists (PATH_peak): os.remove (PATH_peak)
    #if os.path.exists (PATH_out): os.remove (PATH_out)
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

    cmd = request.form.get('cmd', 'quit\n')

    clean_output_folder ()
    result = exec_run_cmd (cmd)

    if os.path.exists (PATH_out):
        response = send_file_with_name (PATH_out)
        return response, 200
    else:
        return jsonify({"error": "出力ファイルがありません"}), 500

@app.route ('/get_xml', methods = ['POST'])
def get_xml ():
    path = search_file ('xml')
    if path is not None:
        response = send_file_with_name (path)
        return response, 200
    else:
        return jsonify ({'error' : 'No output file'})

@app.route ('/get_histogramIgor', methods = ['POST'])
def get_histogramIgor ():
    path = search_file ('histogramIgor')
    if path is not None:
        response = send_file_with_name (path)
        return response, 200
    else:
        return jsonify ({'error' : 'No output file'}), 500

@app.route ('/log_file', methods = ['POST'])
def log_file ():
    if os.path.exists (PATH_log):
        response = send_file_with_name (PATH_log)
        return response, 200
    else:
        return jsonify ({'error' : '送信ファイルがありません'}), 500

@app.route ('/get_output_zip', methods = ['POST'])
def get_output_zip ():
    if os.path.exists (PATH_zip):
        os.remove (PATH_zip)

    shutil.make_archive('archive', format = 'zip',
                root_dir = PATH_output)

    if os.path.exists (PATH_zip):
        response = send_file_with_name (PATH_zip)
        return response, 200
    else:
        return jsonify ({'error' : '送信ファイルがありません'}), 500
    

if __name__ == '__main__':
    app.run(host="0.0.0.0", port = 8100, debug = False)
