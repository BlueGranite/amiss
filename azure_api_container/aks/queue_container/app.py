from flask import Flask, request, jsonify, Response
from datetime import datetime
import os, json, random
from uuid import uuid4
import base64
from azure.storage.queue import QueueServiceClient

app = Flask(__name__)

task_pid = None
session_statuses = {}

service = QueueServiceClient(account_url="https://genomicsdatalake.queue.core.windows.net/", 
                             credential="gfHgyeOy7iWjXKi9p2ijKCgnzVR1Da8/pXtQTkHUHGqhWVrCOGhqfI1ifbDxTZ/sFCg/u/JnQIstA/BcUD8mUA==")

queue_name = "amissqueue"
queue_client = service.get_queue_client(queue_name)



def update_status(sessionid, pid, status, pipe, task, message = ''):

    new_status = {'sessionid': sessionid,
                  'pid': pid,
                  'status': status,
                  'pipe': pipe,
                  'task': task,
                  'message': message,
                  'last_updated': datetime.now().strftime('%x %X')}
    
    session_statuses[sessionid] = new_status

def create_session_task(task, sessionid, session_task_id, param_set):
    session_task = {}
    session_task['task'] = task
    session_task['sessionid'] = sessionid
    session_task['session_task_id'] = session_task_id
    session_task['param_set'] = param_set

    ## Write message to Queue
    queue_client.send_message(json.dumps(session_task))

def sample_params(parameter_grid):

    # parameter_grid = json.dumps(parameter_grid)
    params = {}
    for param in parameter_grid.keys():
        params[param] = random.sample(parameter_grid[param], 1)[0]

    print(params)
    return params

@app.route('/')
def index():
    return 'Blueprint Genetics - AKS Queue'


@app.route('/api/status', methods=['POST'])
def post_status():
    req_body = request.json

    status = req_body['status']

    update_status(sessionid = status['sessionid'],
                  pid = status['pid'],
                  status = status['status'],
                  pipe = status['pipe'],
                  task = status['task'],
                  message = status['message'])

    return jsonify({'response': 'Status updated'})    


@app.route('/api/status', methods=['GET'])
def get_status():
    sessionid = request.args.get('sessionid')

    if sessionid in session_statuses.keys():
        ## Return the updated status
        output = session_statuses[sessionid]
        # output = {k:v for (k,v) in session_statuses[sessionid].items() if 'pipe' not in k}
        return Response(json.dumps(output), 200, mimetype='application/json')
    else:
        return Response("Invalid sessionid.", 400)


@app.route('/api/statuses', methods=['GET'])
def get_statuses():
    return Response(json.dumps(session_statuses), 200, mimetype='application/json')
    
@app.route('/api/amiss', methods = ['POST'])
def run_amiss():
    
    req_body = request.json

    ## Get task info
    task = req_body['task']

    experiment_spec = task['experiment_spec']
    n_combinations = experiment_spec['n_combinations']

    parameter_grid = task['parameter_grid']

    ## Make Unique Session ID
    sessionid = datetime.now().strftime('%Y%m%d%H%M%S_') + str(uuid4())

    for combo in range(0, n_combinations):
        param_set = sample_params(parameter_grid)

        create_session_task(task = 'amiss',
                            sessionid = sessionid,
                            session_task_id = combo + 1,
                            param_set = param_set)

    update_status(sessionid = sessionid,
                #   pid = amiss_pipe.pid, status = 'Submitted', \
                #   pipe = amiss_pipe,
                  pid = -1,
                  status = 'Queued',
                  pipe = None,
                  task = task,
                  message = '')

    output = {'task': 'amiss',
              'sessionid': sessionid,
            #   'pid': amiss_pipe.pid,
              'message': 'Task submitted successfully.'}

    return Response(json.dumps(output), 200, mimetype='application/json')


# @app.route('/api/amiss', methods=['GET'])
# def update_queue():

#     output = {'response': 'No tasks with Status "Queued"'}

#     ## Find first "Queued" item
#     for sessionid in session_statuses.keys():
#         if session_statuses[sessionid]['status'] == 'Queued':
#             output = session_statuses[sessionid]

#             print(output)

#             update_status(sessionid = sessionid,
#                             pid = -1,
#                             status = 'Sent to Cluster',
#                             pipe = None,
#                             task = session_statuses[sessionid]['task'],
#                             message = '')
#             break

#     return jsonify(output)

@app.route('/api/dequeue', methods=['GET'])
def dequeue():

    message = queue_client.receive_message()
    if message is not None:
        queue_client.delete_message(message)
        output = json.loads(message.content)

        print(output)

        update_status(sessionid = output['sessionid'],
                      pid = 1,
                      status = 'Running',
                      pipe = None,
                      task = output['task'],
                      message = '')

    else:
        output = None
        
    return jsonify(output)    

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
