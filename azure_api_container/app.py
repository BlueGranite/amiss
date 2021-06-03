from flask import Flask, request, jsonify, Response
import logging
import subprocess
import json
import os
import yaml
from multiprocessing import cpu_count
from urllib.parse import unquote
from azure.storage.filedatalake import DataLakeServiceClient, DataLakeFileClient
from datetime import datetime
from uuid import uuid4

app = Flask(__name__)

task_pid = None
session_statuses = {}

def update_status(sessionid, pid, status, pipe, message = ''):

    new_status = {'sessionid': sessionid,
                  'pid': pid,
                  'status': status,
                  'pipe': pipe,
                  'message': message,
                  'last_updated': datetime.now().strftime('%x %X')}
    
    session_statuses[sessionid] = new_status


@app.route('/')
def index():
    return 'Blueprint Genetics - amiss Framework'


@app.route('/api/status', methods=['GET'])
def get_status():
    sessionid = request.args.get('sessionid')

    if sessionid in session_statuses.keys():
        ## Pull subprocess' pipe status and message
        pipe = session_statuses[sessionid]['pipe']
        code = pipe.poll() # pipe.returncode
        print("Current status code: ", code)

        # message = ''
        message = os.popen("tail -n 500 /app/amiss/output/" + sessionid + "/step_01.log").read()

        if code == 0:
            status = "Completed"
            # outputlines = pipe.stdout.readlines()
            # message = " ".join([str(i.decode('utf-8')) for i in outputlines])
        elif code == 1:
            status = "Error"
            # pipe_res = pipe.communicate()
            # message = pipe_res[1].decode("utf-8")
            # outputlines = pipe.stderr.readlines()
            # message = " ".join([str(i.decode('utf-8')) for i in outputlines])
        else:
            status = "Running"
            # outputlines = pipe.stdout.readlines()
            # message = " ".join([str(i.decode('utf-8')) for i in outputlines])
        
        ## Update the session ID's status based on the pipe's response
        update_status(sessionid, pipe.pid, status, pipe, message)

        ## Return the updated status
        output = session_statuses[sessionid]
        output = {k:v for (k,v) in session_statuses[sessionid].items() if 'pipe' not in k}
        return Response(json.dumps(output), 200, mimetype='application/json')
    else:
        return Response("Invalid sessionid.", 400)


@app.route('/api/amiss', methods = ['POST'])
def run_amiss():
    
    req_body = request.json

    ## Get Data Lake Connection Ready
    dl_account = req_body['account_url']
    dl_key = req_body['account_credential']
    dl_container = req_body['container']
    dl_suffix = "core.windows.net"
    dl_cnxn = "DefaultEndpointsProtocol=https;AccountName=" + dl_account + ";AccountKey=" + dl_key + ";EndpointSuffix=" + dl_suffix

    serv = DataLakeServiceClient.from_connection_string(conn_str = dl_cnxn)
    fs_client = serv.get_file_system_client(dl_container)

    ## Get task info
    task = req_body['task']

    vcf_path = task['vcf_path']
    cadd_snv_path = task['cadd_snv_path']
    cadd_indel_path = task['cadd_indel_path']

    ## Make Unique Session ID
    sessionid = datetime.now().strftime('%Y%m%d%H%M%S_') + str(uuid4())

    ## Download Files
    dest_dir = '/app/amiss/output/' + sessionid + '/' #f'/app/amiss/output/{sessionid}/'

    for task_file in [vcf_path, cadd_snv_path, cadd_indel_path]:
        file_client = fs_client.get_file_client(task_file)

        task_file_path = os.path.basename(task_file)

        dest_path = os.path.dirname(os.path.join(dest_dir, task_file_path))
        dest_path_file =  os.path.join(dest_dir, task_file_path)
        os.makedirs(dest_path, exist_ok = True)

        with open(dest_path_file, 'wb') as local_file:
            file_client.download_file().readinto(local_file)

    ## Define environment variables
    rel_dir = 'output/' + sessionid + '/'

    os.environ['AMISS_SESSION_ID'] = sessionid
    os.environ['AMISS_SESSION_DIR'] = rel_dir
    os.environ['AMISS_VCF_FILENAME'] = rel_dir + os.path.basename(vcf_path)
    os.environ['AMISS_CADD_SNV_FILENAME'] = rel_dir + os.path.basename(cadd_snv_path)
    os.environ['AMISS_CADD_INDEL_FILENAME'] = rel_dir + os.path.basename(cadd_indel_path)


    amiss_cmd = ["/bin/sh", "run.sh"]#,
                # sessionid,
                # dest_dir,
                # dest_dir + os.path.basename(vcf_path),
                # dest_dir + os.path.basename(cadd_snv_path),
                # dest_dir + os.path.basename(cadd_indel_path)]

    amiss_pipe = subprocess.Popen(amiss_cmd, \
                                  stdout=subprocess.PIPE, \
                                  stderr=subprocess.PIPE)

    update_status(sessionid = sessionid, pid = amiss_pipe.pid, status = 'Submitted', \
                  pipe = amiss_pipe, message = '')

    ## TEMPORARY: Show that files have been downloaded
    # output_files = 0
    # for base, dirs, files in os.walk(dest_dir):
    #     for Files in files:
    #         output_files += 1

    # output = {'files downloaded': output_files, "sessionid": sessionid}
    
    # return jsonify({"response": output})

    output = {'task': 'amiss',
              'sessionid': sessionid,
              'pid': amiss_pipe.pid,
              'message': 'Task submitted successfully.'}

    return Response(json.dumps(output), 200, mimetype='application/json')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)