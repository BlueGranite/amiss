from kubernetes import client, config
import yaml

# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

v1 = client.CoreV1Api()

# res = v1.list_namespaced_pod(namespace = "default")
# res.items[0].status.phase

v1.delete_namespaced_pod("helloer", namespace = "default")

with open("pod.yaml", "r") as f:
    dep = yaml.safe_load(f)

v1 = client.CoreV1Api()
resp = v1.create_namespaced_pod(body=dep, namespace="default")
print("Deployment created. status='%s'" % resp.metadata.name)

