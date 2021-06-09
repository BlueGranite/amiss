from azure.storage.filedatalake import DataLakeServiceClient
from azure.identity import DefaultAzureCredential

from kubernetes import client as kube_client
from kubernetes import config as kube_config
from kubernetes.client.exceptions import ApiException

import yaml
import json
import os
import logging

logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("setup_kubernetes")
logger.setLevel(logging.INFO)

## Get kubernetes client
kube_config.load_kube_config()
kube_v1_client = kube_client.CoreV1Api()

# Get basic Azure config stuff from config yaml
with open(sys.argv[2], "r") as i:
    pod_config = yaml.safe_load(i)
subscription_id = pod_config["azure_subscription_id"]
resource_group = pod_config["azure_resource_group"]
queue_url = pod_config["azure_queue_storage_url"]

# Basic validation
validation_errors = 0
specified_analysis_types = pod_config["analysis_types"]

## First validation - make sure there is a pod definition for each analysis type and visa versa
analysis_pod_definitions = [d.replace(".yaml", "") for d in os.listdir(os.path.join(os.path.dirname(__file__), 'analysis_pod_definitions'))]

for k, v in specified_analysis_types.items():
    if k not in analysis_pod_definitions:
        validation_errors += 1
        logger.error("Expected pod definition {}.yaml - did not find".format(k))

for p in analysis_pod_definitions:
    if p not in specified_analysis_types.keys():
        validation_errors += 1
        logger.error("Expected analysis type {} based on presence of pod definition {}.yaml".format(k))


## Second validation - make sure that each analysis type pod has correct tolerations and selectors set
for p in analysis_pod_definitions:
    with open(p) as p_in:
        pod = yaml.safe_load(p_in)
    
    # Tolerations
    try:
        tolerations = {t["key"]:t for t in pod["spec"]["tolerations"]}
        if "pipeline" not in tolerations.keys():
            validation_errors += 1
            logger.error("Expected pipeline toleration for pod definition {}.yaml - did not find".format(p))
        else:
            if (tolerations["pipeline"]["value"] != p) or (tolerations["pipeline"]["operator"] != "Equal"):
                validation_errors += 1
                logger.error("Toleration for pod definition {}.yaml is incorrectly configured".format(p))
    except KeyError:
        validation_errors += 1
        logger.error("Toleration for pod definition {}.yaml is incorrectly configured".format(p))

    # Selectors
    try:
        selectors = pod["spec"]["nodeSelector"]
        if "pipeline" not in selectors.keys():
            validation_errors += 1
            logger.error("Expected pipeline selector for pod definition {}.yaml - did not find".format(p))
        else:
            if selectors["pipeline"] != p:
                validation_errors += 1
                logger.error("Pipeline selector for pod definition {}.yaml is incorrectly configured".format(p))
    except KeyError:
        validation_errors += 1
        logger.error("Pipeline selector for pod definition {}.yaml is incorrectly configured".format(p))
    


## Pull in the kubernetes config stuff
kube_v1_client.create_namespaced_secret()

kubernetes_instance_config = os.getenv("AZURE_KUBERNETES_CONFIG")
kubernetes_instance_config_pod_types = kubernetes_instance_config + "pod_types.yaml"
kubernetes_pod_types_yaml = fs_client.get_file_client(kubernetes_instance_config_pod_types)\
                                     .download_file()\
                                     .readall()
kubernetes_pod_types = yaml.safe_load(kubernetes_pod_types_yaml)

resp = v1.create_namespaced_pod(body=pod, namespace="default", async_req = False)