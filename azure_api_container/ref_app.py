from flask import Flask, request, jsonify, Response
import logging
import subprocess
import json
from datetime import datetime
from uuid import uuid4
import os
import yaml
from multiprocessing import cpu_count
from urllib.parse import unquote
from azure.storage.filedatalake import DataLakeServiceClient, DataLakeFileClient
import shlex
# from threading  import Thread
# from queue import Queue, Empty

app = Flask(__name__)
snakemake_pid = None
session_statuses = {}

@app.route('/')
def index():
    return 'Bioinformatics.'

def update_status(sessionid, pid, status, pipe, message = ''):

    new_status = {'sessionid': sessionid,
                  'pid': pid,
                  'status': status,
                  'pipe': pipe,
                  'message': message,
                  'last_updated': datetime.now().strftime('%x %X')}
    
    session_statuses[sessionid] = new_status

@app.route('/status', methods=['GET'])
def get_status():
    sessionid = request.args.get('sessionid')

    if sessionid in session_statuses.keys():
        ## Pull subprocess' pipe status and message
        pipe = session_statuses[sessionid]['pipe']
        code = pipe.poll() # pipe.returncode
        print("Current status code: ", code)

        # message = ''
        message = os.popen(f"tail -n 25 /tmp/sessiondata/{sessionid}/snakemake.log").read()

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
    

@app.route('/RNAseqPipeline', methods=['POST'])
def run_snakemake():
    
    req_body = request.json
    # run_params = req_body['params']

    mountpoint = os.environ['AZURE_MOUNT_POINT']

    ## Make Unique Session ID
    sessionid = datetime.now().strftime('%Y%m%d%H%M%S_') + str(uuid4())

    ## Get References 
    reference_set = req_body['reference_set']
    reference_yml = f"{mountpoint}/references/.reference-sets/{reference_set}.yaml"
    
    ## Get input info
    project = req_body['project']
    study = req_body['study']
    sample = req_body['sample']
    analysistype = "RNAseq" # run_params['analysistype']
    base_path = f"{mountpoint}/project_data/{project}/{study}/{analysistype}/{sample}/readgroups"
    completed_path = f"{mountpoint}/project_data/{project}/{study}/{analysistype}/{sample}/completed/"
    
    print("Using Base Path: ", base_path)

    ## Set output dir
    outprefix = f"/tmp/sessiondata/{sessionid}"
    os.makedirs(outprefix, exist_ok=True)
    # os.symlink(outprefix, f"/outputs/{sessionid}") # This is just a lazy hack to 
    # os.symlink(outprefix, "/outputs") # This is just a lazy hack to 
    # os.makedirs(os.path.dirname(outprefix + "/output/"), exist_ok=True)
    
    ## Get machine info
    mem = os.environ.get("MEMGIG") # 64000000000
    threads = str(os.cpu_count()) #os.environ.get("NCPU")
    
    ### Snakemake command
    # snakemake_cmd = ["snakemake",
    #                  "--cores", f"{threads}",
    #                  "--config", f"NCPU={threads}",
    #                              f"SAMPLE_ID={sample}",
    #                              f"INPUTS_PATH={base_path}",
    #                              f"MOUNTPOINT={mountpoint}",
    #                              f"REFERENCE_YAML_PATH={reference_yml}",
    #                  "--resources", f"mem={mem}",
    #                  "--snakefile", "Snakefile",
    #                  #">", "/outputs/snakemake.log", #"2>&1",
    #                  ";", f"mkdir -p {completed_path}",
    #                  ";", f"rsync -r {outprefix} {completed_path}"]

    # snakemake_cmd = ["snakemake", "--version"]


    # snakemake_cmd = " ".join([str(i) for i in snakemake_cmd])
    # os.system(snakemake_cmd)

    # return("RNAseq Pipeline Task Submitted Successfully.")
    # snakemake_pid = subprocess.Popen(snakemake_cmd).pid

    # snakemake_cmd = shlex.split(" ".join([str(i) for i in snakemake_cmd]))

    ## Define environment variables
    os.environ['threads'] = threads
    os.environ['mem'] = mem
    os.environ['sample'] = sample
    os.environ['base_path'] = base_path
    os.environ['mountpoint'] = mountpoint
    os.environ['reference_yml'] = reference_yml
    os.environ['outprefix'] = outprefix
    os.environ['completed_path'] = completed_path


    snakemake_cmd = ['/bin/sh', 'run_snakemake.sh']

    print("Snake Command: ", snakemake_cmd)

    snakemake_pipe = subprocess.Popen(snakemake_cmd, \
                                      stdout=subprocess.PIPE, \
                                      stderr=subprocess.PIPE)

    update_status(sessionid = sessionid, pid = snakemake_pipe.pid, status = 'Submitted', \
                  pipe = snakemake_pipe, message = '')

    # subprocess.run(snakemake_cmd)

    output = {'task': 'RNAseqPipeline',
              'sessionid': sessionid,
              'pid': snakemake_pipe.pid,
              'message': 'Task submitted successfully.'}

    return Response(json.dumps(output), 200, mimetype='application/json')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)