# Using some code from https://github.com/Azure-Samples/resource-manager-python-template-deployment

import os
import json
import yaml
import sys
import logging
import re
from haikunator import Haikunator

from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import DeploymentMode, DeploymentProperties, Deployment
from azure.storage.queue import QueueServiceClient

logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("setup_aks")
logger.setLevel(logging.INFO)

# Get basic Azure config stuff from config yaml
with open(sys.argv[2], "r") as i:
    pod_config = yaml.safe_load(i)
subscription_id = pod_config["azure_subscription_id"]
resource_group = pod_config["azure_resource_group"]
queue_url = pod_config["azure_queue_storage_url"]

# Set up clients needed for deployment
name_generator = Haikunator()
cred = AzureCliCredential()
arm_client = ResourceManagementClient(cred, subscription_id, api_version="2018_02_01")
queue_client = QueueServiceClient(queue_url, cred)

# Get template
with open(os.path.join(os.path.dirname(__file__), 'azure', 'template.json'), 'r') as t:
    template = json.load(t)

# Get parameters
with open(os.path.join(os.path.dirname(__file__), 'azure', 'parameters.json'), 'r') as p:
    parameters = json.load(p)

# Basic validation
validation_errors = 0
specified_analysis_types = pod_config["analysis_types"]
aks_resource = [r for r in template["resources"] if r["type"] == "Microsoft.ContainerService/managedClusters"][0]
aks_nodepools = {p["name"]:p for p in aks_resource["properties"]["agentPoolProfiles"]}
active_queues = [q.name for q in queue_client.list_queues()]


## First validation - make sure that the analysis types specified in the configuration are matched by 
## a nodepool specification in the in the ARM template and that the max node count is correct.
for k,v in specified_analysis_types.items():
    pool_name = "{}pool".format(k)
    if pool_name in aks_nodepools.keys():
        nodepool_properties = aks_nodepools[pool_name]
        if v["max_nodes"] != nodepool_properties["maxCount"]:
            validation_errors += 1
            logger.error("Mismatch between specified node count {} for analysis type {} and ARM specification {} for {}"\
                .format(v["max_nodes"], k, nodepool_properties["maxCount"], pool_name))
    else:
        validation_errors += 1
        logger.error("Analysis type {} specified in configuration but no {} nodepool present in ARM template".format(k, pool_name))


## Second validation - make sure all the nodepool specifications in the ARM template are specified in the config,
## that they have correct mincount and count and that they have the correct labels and taints.
for k, nodepool_properties in aks_nodepools.items():
    analysis_type_name = k.replace("pool", "")
    if analysis_type_name in specified_analysis_types.keys():
        if nodepool_properties["minCount"] > 0:
            validation_errors += 1
            logger.error("For nodepool {} in ARM specification mincount is {} - it should be 0"\
                .format(k, nodepool_properties["minCount"]))
        if nodepool_properties["count"] > 0:
            validation_errors += 1
            logger.error("For nodepool {} in ARM specification count is {} - it should be 0"\
                .format(k, nodepool_properties["count"]))

        # Make sure node labels are correct
        try:
            if nodepool_properties["nodeLabels"]["pipeline"] != analysis_type_name:
                validation_errors += 1
                logger.error("For nodepool {} in ARM specification 'pipeline' node label is {} - should be {}"\
                    .format(k, nodepool_properties["nodeLabels"]["pipeline"], analysis_type_name))
        except KeyError:
            validation_errors += 1
            logger.error("For nodepool {} in ARM specification node label is incorrectly specified.".format(k))

        # Make sure node taints are correct
        try:
            for t in nodepool_properties["nodeTaints"]:
                m = re.search("pipeline=(\w+):NoSchedule", t)
                if m:
                    if m.group(1) != analysis_type_name:
                        validation_errors += 1
                        logger.error("For nodepool {} in ARM specification node taint is {} - should be {}.".format(k, m.group(1), analysis_type_name))
                else:
                    validation_errors += 1
                    logger.error("For nodepool {} in ARM specification node taint is incorrectly specified.".format(k))
        except KeyError:
            validation_errors += 1
            logger.error("For nodepool {} in ARM specification node taint is incorrectly specified.".format(k))

    elif k == "agentpool":
        if nodepool_properties["count"] != 1:
            validation_errors += 1
            logger.error("For nodepool {} in ARM specification count is {} - it should be 1"\
                .format(k, nodepool_properties["count"]))
    else:
        validation_errors += 1
        logger.error("Nodepool type {} specified in ARM template but no analysis type {} specified in config".format(k, analysis_type_name))


## Third validation - make sure that for each analysis type there is an active storage queue
for k,v in specified_analysis_types.items():
    queue_name = "{}queue".format(k)
    if queue_name not in active_queues:
        validation_errors += 1
        logger.error("Analysis type {} specified in configuration but no {} storage queue present in Azure".format(k, queue_name))

## The deployment from the python API just doesn't work - there is a problem with the serialization and MS has seemingly
## abandoned this - multiple breaking changes in API, they just don't seem to care.
## the solution for now is that we just deploy using the CLI
# if sys.argv[1] == "deploy" and validation_errors == 0:
    # New way
    # deployment_properties = DeploymentProperties(mode=DeploymentMode.incremental, 
    #                                              template=template, 
    #                                              parameters=parameters)
    # deployment_object = Deployment(location="uswest2", properties=deployment_properties)
    # arm_client.deployments.begin_validate(resource_group, 
    #                                       "aks-deployment-{}".format(name_generator.haikunate()),
    #                                       deployment_object)

    # Old way
    # deployment_properties = {"properties": {"mode": DeploymentMode.incremental, "template": template, "parameters": parameters}}
    # validation = arm_client.deployments.validate(resource_group, "aks-deployment-{}".format(name_generator.haikunate()), deployment_properties)


#     deployment = arm_client.deployments.begin_create_or_update(resource_group, 
#                                                                "aks-deployment-{}".format(name_generator.haikunate()),
#                                                                deployment_object)
#     deployment.wait()

#     print(deployment.result().properties.outputs)
