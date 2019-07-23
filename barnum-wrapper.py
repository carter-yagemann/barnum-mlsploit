import math
import json
import os
import sys
import subprocess
import shutil
from tempfile import mkdtemp
from zipfile import ZipFile

def evaluation(job):
    # Input validation
    if job['num_files'] != len(job['files']):
        sys.stderr.write("num_files != actual number of files (%d v.s. %d)\n" % (job['num_files'], len(job['files'])))
        sys.exit(1)
    for filepath in job['files']:
        fullpath = os.path.join('/mnt/input', filepath)
        if not os.path.isfile(fullpath):
            sys.stderr.write("Failed to find trace " + fullpath + "\n")
            sys.exit(1)
    if not os.path.isfile('/mnt/input/model.zip'):
        sys.stderr.write("Cannot find model file: /mnt/input/model.zip\n")
        sys.exit(1)

    # Preparation (i.e. unzip all the things!)
    work_dir = mkdtemp()
    traces_dir = os.path.join(work_dir, 'traces')
    model_dir = os.path.join(work_dir, 'model')
    eval_dir = os.path.join(work_dir, 'eval')
    os.mkdir(traces_dir)
    os.mkdir(model_dir)
    os.mkdir(eval_dir)

    trace_info = dict()
    for filename in job['files']:
        if filename == 'model.zip':
            continue  # model file is special, processed later
        fullpath = os.path.join('/mnt/input', filename)
        # any files we tag must be in the output directory, even if content is unchanged
        shutil.copy(fullpath, '/mnt/output')
        try:
            with ZipFile(fullpath, 'r') as ifile:
                trace_name = ifile.namelist()[0].replace('/', "")
                trace_info[trace_name] = {
                           'zip': filename,
                           'name': trace_name,
                           'path': os.path.join(traces_dir, trace_name),
                           'tag': None}
                ifile.extractall(traces_dir)
                # Get real label
                info_file = os.path.join(trace_info[trace_name]['path'], 'info.txt')
                with open(info_file, 'r') as info_fd:
                    trace_info[trace_name]['tag'] = info_fd.readlines()[-1].strip()
        except Exception as ex:
            sys.stderr.write("Failed to unzip file: " + str(ex) + "\n")
            sys.exit(1)
    try:
        fullpath = '/mnt/input/model.zip'
        with ZipFile(fullpath, 'r') as ifile:
            ifile.extractall(model_dir)
    except Exception as ex:
        sys.stderr.write("Failed to unzip model: " + str(ex) + "\n")
        sys.exit(1)

    # Make set list for Barnum
    with open(os.path.join(work_dir, 'set.txt'), 'w') as ofile:
        ofile.write("[b_test]\n")
        for trace in trace_info:
            if trace_info[trace]['tag'] == 'benign':
                ofile.write(trace_info[trace]['path'] + "\n")
        ofile.write("[m_test]\n")
        for trace in trace_info:
            if trace_info[trace]['tag'] == 'malicious':
                ofile.write(trace_info[trace]['path'] + "\n")

    # Run the LSTM layer
    cmd = ['/usr/bin/python3', '/app/barnum/lstm.py', '--skip-test', '--eval-dir', eval_dir, '-p', '-i',
           os.path.join(work_dir, 'set.txt'), '--use-model', os.path.join(model_dir, 'lstm.json'),
           '--use-weights', os.path.join(model_dir, 'lstm.h5'), traces_dir]
    ret = subprocess.call(cmd, stdout=sys.stdout, stderr=sys.stderr)
    if ret != 0:
        sys.stderr.write("lstm.py returned error code\n")
        sys.exit(ret)

    # Run the classification layer
    csv_fp = os.path.join(work_dir, 'out.csv')
    cmd = ['/usr/bin/python3', '/app/barnum/classifier.py', '-l', os.path.join(model_dir, 'svm'), '-c', csv_fp, eval_dir]
    ret = subprocess.call(cmd, stdout=sys.stdout, stderr=sys.stderr)
    if ret != 0:
        sys.stderr.write("classifier.py returned error code\n")
        sys.exit(ret)

    # Parse the results to make output.json
    with open(csv_fp, 'r') as ifile:
        header = ifile.readline()  # Skip the CSV header
        for line in ifile:
            true, pred, avg_acc, avg_con, name = line.strip().split(',')
            # Strip off the file extension and prefix to match trace_info key
            # Example name: benign-607aad68f9f2683a4a76b858bff3247018b33918b0f4d5144aaafb928388bb06.gz
            name = name.split('.')[0].split('-')[1]
            if pred == '1':
                trace_info[name]['pred'] = 'malicious'
            else:
                trace_info[name]['pred'] = 'benign'

    res = {"name": "Barnum-Eval", "files": [], "files_extra": [], "files_modified": [], "tags": []}
    for info in trace_info:
        res["files"].append(trace_info[info]['zip'])
        if 'pred' in trace_info[info].keys():
            res["tags"].append({"real_label": trace_info[info]['tag'], "pred_label": trace_info[info]['pred']})
        else:
            res["tags"].append({"real_label": trace_info[info]['tag'], "pred_label": trace_info[info]['tag']})

    with open('/mnt/output/output.json', 'w') as ofile:
        json.dump(res, ofile)

def train(job):
    # Input validation
    if job['num_files'] != len(job['files']):
        sys.stderr.write("num_files != actual number of files (%d v.s. %d)\n" % (job['num_files'], len(job['files'])))
        sys.exit(1)
    for filepath in job['files']:
        fullpath = os.path.join('/mnt/input', filepath)
        if not os.path.isfile(fullpath):
            sys.stderr.write("Failed to find trace " + fullpath + "\n")
            sys.exit(1)

    # Preparation
    work_dir = mkdtemp()
    traces_dir = os.path.join(work_dir, 'traces')
    model_dir = os.path.join(work_dir, 'model')
    eval_dir = os.path.join(work_dir, 'eval')
    os.mkdir(traces_dir)
    os.mkdir(model_dir)
    os.mkdir(eval_dir)

    trace_info = dict()
    for filename in job['files']:
        fullpath = os.path.join('/mnt/input', filename)
        # any files we tag must be in the output directory, even if content is unchanged
        shutil.copy(fullpath, '/mnt/output')
        try:
            with ZipFile(fullpath, 'r') as ifile:
                trace_name = ifile.namelist()[0].replace('/', "")
                trace_info[trace_name] = {
                           'zip':  filename,
                           'name': trace_name,
                           'path': os.path.join(traces_dir, trace_name),
                           'tag':  None}
                ifile.extractall(traces_dir)
                # Get real label
                info_file = os.path.join(trace_info[trace_name]['path'], 'info.txt')
                with open(info_file, 'r') as info_fd:
                    trace_info[trace_name]['tag'] = info_fd.readlines()[-1].strip()
        except Exception as ex:
            sys.stderr.write("Failed to unzip file: " + str(ex) + "\n")
            sys.exit(1)

    # Use ~90% of benign for training, rest for testing (Barnum LSTM doesn't train or test on mal traces)
    tags = [trace_info[info]['tag'] for info in trace_info]
    num_b = len([tag for tag in tags if tag == 'benign'])
    num_m = len([tag for tag in tags if tag == 'malicious'])
    if num_b < 2:
        sys.stderr.write("Need at least two benign traces to train and test LSTM layer\n")
        sys.exit(1)
    if num_m < 1:
        sys.stderr.write("Need at least one malicious trace to train classification layer\n")
        sys.exit(1)
    num_b_train = int(math.floor(float(num_b) * 0.9))
    num_b_test = num_b - num_b_train

    # Run the LSTM layer
    cmd = ['/usr/bin/python3', '/app/barnum/lstm.py', '-p', '--eval-dir', eval_dir, '--train-size', str(num_b_train),
           '--test-size-benign', str(num_b_test), '--test-size-malicious', str(num_m),
           '--save-model', os.path.join(model_dir, 'lstm.json'), '--save-weights', os.path.join(model_dir, 'lstm.h5'),
           '--checkpoint', '60', '--checkpoint-best', '-e', str(job['options']['epoch']), traces_dir]
    ret = subprocess.call(cmd, stdout=sys.stdout, stderr=sys.stderr)
    if ret != 0:
        sys.stderr.write("lstm.py returned error code\n")
        sys.exit(ret)

    # Run the classification layer
    csv_fp = os.path.join(work_dir, 'out.csv')
    cmd = ['/usr/bin/python3', '/app/barnum/classifier.py', '-s', os.path.join(model_dir, 'svm'), '-c', csv_fp, eval_dir]
    ret = subprocess.call(cmd, stdout=sys.stdout, stderr=sys.stderr)
    if ret != 0:
        sys.stderr.write("classifier.py returned error code\n")
        sys.exit(ret)

    # Parse the results to make output.json and model.zip
    with ZipFile('/mnt/output/model.zip', 'w') as ofile:
        ofile.write(os.path.join(model_dir, 'lstm.json'), 'lstm.json')
        ofile.write(os.path.join(model_dir, 'lstm.h5'), 'lstm.h5')
        ofile.write(os.path.join(model_dir, 'svm'), 'svm')

    with open(csv_fp, 'r') as ifile:
        header = ifile.readline()  # Skip the CSV header
        for line in ifile:
            true, pred, avg_acc, avg_con, name = line.strip().split(',')
            # Strip off the file extension and prefix to match trace_info key
            # Example name: benign-607aad68f9f2683a4a76b858bff3247018b33918b0f4d5144aaafb928388bb06.gz
            name = name.split('.')[0].split('-')[1]
            if pred == '1':
                trace_info[name]['pred'] = 'malicious'
            else:
                trace_info[name]['pred'] = 'benign'

    res = {"name": "Barnum-Train", "files": ["model.zip"], "files_extra": ["model.zip"], "files_modified": [], "tags": [{}]}
    for info in trace_info:
        res["files"].append(trace_info[info]['zip'])
        if 'pred' in trace_info[info].keys():
            res["tags"].append({"real_label": trace_info[info]['tag'], "pred_label": trace_info[info]['pred']})
        else:
            res["tags"].append({"real_label": trace_info[info]['tag'], "pred_label": trace_info[info]['tag']})

    with open('/mnt/output/output.json', 'w') as ofile:
        json.dump(res, ofile)

if __name__ == '__main__':
    try:
        with open('/mnt/input/input.json', 'r') as ifile:
            job = json.load(ifile)
    except Exception as ex:
        sys.stderr.write("Failed to open input.json: " + str(ex) + "\n")
        sys.exit(1)

    if job['name'] == 'Barnum-Eval':
        evaluation(job)
    elif job['name'] == 'Barnum-Train':
        train(job)
    else:
        sys.stderr.write("Unsupported function: " + job['name'] + "\n")
        sys.exit(1)
