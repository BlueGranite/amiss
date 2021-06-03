# FROM phusion/baseimage:18.04-1.0.0

FROM rocker/r-ver:3.6.0
RUN apt-get update && \
	apt-get install -y zlib1g-dev && \
	apt-get install -y libcurl4-openssl-dev && \
	rm -rf /var/lib/apt/lists/*

COPY ./R/install_packages.R /app/amiss/R/install_packages.R
RUN Rscript /app/amiss/R/install_packages.R
COPY . /app/amiss

LABEL authors="Colby Ford <cford@bluegranite.com>"

ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev && \
    ln -s /usr/bin/python3 python && \
    pip3 --no-cache-dir install --upgrade pip && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/amiss/
ADD . /app/amiss/.
RUN chmod 755 /app/amiss/

RUN pip3 install --no-cache-dir -r /app/amiss/requirements.txt

WORKDIR /app/amiss/

EXPOSE 5000


CMD [ "python3", "app.py" ]