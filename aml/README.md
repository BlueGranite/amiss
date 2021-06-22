
```
docker build -t amiss_aml .

docker run --name amiss_aml --rm -p 8787:8787 amiss_aml

docker image tag amiss_aml cford38/amiss_aml:latest
docker push cford38/amiss_aml:latest
```