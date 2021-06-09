# Azure AKS Repository

This is general repo for everything aroud setting up AKS in Azure for bioinformatics pipelines.

To interact with Azure - install Azure CLI.

To interact with AKS cluster - use kubectl (az aks install-cli)

wget https://github.com/mikefarah/yq/releases/download/v4.9.1/yq_linux_386 -O /usr/local/bin/yq && \
    chmod +x /usr/local/bin/yq

```
python setup_aks.py validate pod_config.yaml

az deployment group create \
  -g sg-bioi-dev-pipelines \
  --template-file azure/template.json \
  --parameters @azure/parameters.json \
  -o json

az aks get-credentials --resource-group sg-bioi-dev-pipelines --name sgbioiaksdemo
```

```
az identity show --resource-group MC_sg-bioi-dev-pipelines_sgbioiaksdemo_westus2 -n omsagent-sgbioiaksdemo --query "clientId"
```

az aks get-credentials --resource-group sg-bioi-dev-pipelines --name sgbioiaksdemo

kubectl apply -f sg_kub.yaml

kubectl get service rnaseq-pipeline --watch

kubectl get pods

kubectl exec --stdin --tty rnaseq-pipeline-598bbbbc8d-lxrbm -- /bin/bash

az aks nodepool list --resource-group sg-bioi-dev-pipelines --cluster-name sgbioiaksdemo

az aks nodepool update \
    --resource-group sg-bioi-dev-pipelines \
    --cluster-name sgbioiaksdemo \
    --name agentpool \
    --labels pipeline=central \
    --no-wait

az aks nodepool update \
    --resource-group sg-bioi-dev-pipelines \
    --cluster-name sgbioiaksdemo \
    --name rnaseqpool \
    --labels pipeline=rnaseq \
    --no-wait

az aks nodepool scale --cluster-name sgbioiaksdemo \
                      --name rnaseqpool \
                      --resource-group sg-bioi-dev-pipelines \
                      --node-count 1

az aks stop --resource-group sg-bioi-dev-pipelines --name sgbioiaksdemo

az aks delete --resource-group sg-bioi-dev-pipelines --name sgbioiaksdemo