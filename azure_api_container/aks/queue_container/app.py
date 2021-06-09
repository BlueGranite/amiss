from flask import Flask, request, jsonify, Response
import base64
from azure.storage.queue import QueueServiceClient

# We need to remove any hard coded keys prior to getting to production, obviously
service = QueueServiceClient(account_url="https://genomicsdatalake.queue.core.windows.net/", 
                             credential="gfHgyeOy7iWjXKi9p2ijKCgnzVR1Da8/pXtQTkHUHGqhWVrCOGhqfI1ifbDxTZ/sFCg/u/JnQIstA/BcUD8mUA==")
queue_client = service.get_queue_client("amissqueue")

app = Flask(__name__)

@app.route('/')
def index():
    return 'Blueprint Genetics - AKS Queue'

@app.route('/dequeue/<queue_name>', methods=['GET'])
def dequeue(queue_name):
    queue_client = service.get_queue_client(queue_name)
    message = queue_client.receive_message() # Message can ==None
    if message is not None:
        queue_client.delete_message(message)
        # content = message.content
        output = message.content
        # try:
        #     output = base64.b64decode(message.content).decode()
        # except UnicodeDecodeError:
        #     output = message.content
    else:
        output = None
        
    return jsonify({"response": output})    

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
