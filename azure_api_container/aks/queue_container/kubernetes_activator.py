from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
import yaml
import json
import os
import logging

from azure.storage.queue import QueueServiceClient

logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("kubernetes_activator")
logger.setLevel(logging.INFO)

script_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(script_dir, "pod_limits.yaml")) as p:
    pod_limits = yaml.safe_load(p)

# We need to remove any hard coded keys prior to getting to production, obviously
service = QueueServiceClient(account_url="https://genomicsdatalake.queue.core.windows.net/", 
                             credential="gfHgyeOy7iWjXKi9p2ijKCgnzVR1Da8/pXtQTkHUHGqhWVrCOGhqfI1ifbDxTZ/sFCg/u/JnQIstA/BcUD8mUA==")

# Set config according to environment
DEVENV = os.getenv('SG_DEV_ENV')
if DEVENV:
    config.load_kube_config()
else:
    config.load_incluster_config()
    
v1 = client.CoreV1Api()

for pod_type_yaml in os.listdir(os.path.join(script_dir, "pods")):
    if pod_type_yaml.endswith(".yaml"):
        pod_type = pod_type_yaml[:-5]
        queue = service.get_queue_client(pod_type)
        metadata = queue.get_queue_properties()
        message_count = metadata.approximate_message_count
        message_count = message_count if message_count < pod_limits[pod_type] else pod_limits[pod_type]
        logger.info(f"Pod Type: {pod_type}\tCount: {message_count}")
        if message_count > 0:
            with open(os.path.join(script_dir, "pods", pod_type_yaml), "r") as p:
                pod = yaml.safe_load(p)
            pod_name = pod["metadata"]["name"]
            for i in range(message_count):
                pod["metadata"]["name"] = f"{pod_name}-{i}"
                try:
                    resp = v1.create_namespaced_pod(body=pod, namespace="default", async_req = False)
                    logger.info("Pod created: '%s'" % resp.metadata.name)
                except ApiException as e:
                    exception_body = json.loads(e.body)
                    if ("reason" in exception_body) and (exception_body["reason"] == "AlreadyExists"):
                        logger.info("Pod creation failure: '%s'" % exception_body["message"])
                    else:
                        raise




