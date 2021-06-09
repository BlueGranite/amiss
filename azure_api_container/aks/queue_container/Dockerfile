FROM phusion/baseimage:18.04-1.0.0

LABEL authors="Colby Ford <cford@bluegranite.com>"

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 --no-cache-dir install --upgrade pip && \
    pip install \
    Flask==1.1.2 \
    azure-storage-queue==12.1.6 \
    kubernetes==12.0.1

RUN curl -o /tmp/kubectl -L "https://dl.k8s.io/release/v1.21.0/bin/linux/amd64/kubectl" && \
    curl -o /tmp/kubectl.sha256 -L "https://dl.k8s.io/v1.21.0/bin/linux/amd64/kubectl.sha256" && \
    echo "$(cat /tmp/kubectl.sha256) /tmp/kubectl" > /tmp/check && \
    sha256sum --check /tmp/check && \
    chmod +x /tmp/kubectl && \
    mv /tmp/kubectl /usr/local/bin/kubectl && \
    rm /tmp/*

RUN mkdir /opt/blueprintgenetics-azure-aks-queue
ADD . /opt/blueprintgenetics-azure-aks-queue/.
RUN chmod 755 /opt/blueprintgenetics-azure-aks-queue/Run.sh

COPY kub_cron /etc/cron.d/kub_cron
RUN chmod 0744 /etc/cron.d/kub_cron && \
    crontab /etc/cron.d/kub_cron

WORKDIR /opt/blueprintgenetics-azure-aks-queue/
CMD [ "python3", "app.py" ]