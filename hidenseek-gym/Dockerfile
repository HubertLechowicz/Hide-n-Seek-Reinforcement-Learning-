FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y python3-pip alsa-utils alsa-oss xvfb ffmpeg python3-dev python-opengl git locales \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip --no-cache-dir

RUN apt-get clean --dry-run

ENV DISPLAY=:0

WORKDIR /opt/app
COPY . /opt/app/
RUN python /opt/app/setup.py install

ENTRYPOINT python3 /opt/app/main.py