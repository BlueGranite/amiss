from kubernetes import client, config
import yaml
import logging
import os

logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("kubernetes_reaper")

# Set config according to environment
DEVENV = os.getenv('SG_DEV_ENV')
if DEVENV:
    config.load_kube_config()
else:
    config.load_incluster_config()

v1 = client.CoreV1Api()

res = v1.list_namespaced_pod(namespace = "default")
for p in res.items:
    if p.status.phase in ["Succeeded", "Failed"]:
        resp = v1.delete_namespaced_pod(p.metadata.name, namespace = "default", async_req = False)
        logger.info(f"{p.metadata.name} delete requested; self_link='{resp.metadata.self_link}'")



