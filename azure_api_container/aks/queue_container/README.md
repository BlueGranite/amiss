## Running in Docker

1. Open terminal and navigate to the directory of this repository.

2. Run the following command, which will generate the Docker image.
```sh
docker build -t bgamiss_queue .
```

3. Once the image has been created successfully, run the container locally using the following command.
```sh
docker run -p 5000:5000 --name bgamiss_queue -it bgamiss_queue
```

Note: You will need to change the `"authLevel": "function"` setting in the _functions.json_ file to `"authLevel": "anonymous"` to test the API in the Docker container locally.

To browse the Docker container, run the following:
```sh
docker exec -it bgamiss_queue /bin/sh
```

4. To push the image to an Azure Container Registry, run the following:

```sh
az login
az account set --subscription 66aa47b7-749d-416e-8db9-b98bc14a07a1

az acr login --name bgamiss

docker tag bgamiss_queue bgamiss.azurecr.io/bgamiss_queue:v1
docker push bgamiss.azurecr.io/bgamiss_queue:v1

```