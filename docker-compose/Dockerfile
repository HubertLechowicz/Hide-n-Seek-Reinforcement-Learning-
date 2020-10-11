FROM python:3.8

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y alsa-utils alsa-oss xvfb ffmpeg python-opengl git locales \
  && cd /usr/local/bin \
  && pip install --upgrade pip --no-cache-dir

RUN apt-get clean --dry-run

ADD req.txt /opt/app/req.txt
WORKDIR /opt/app/
COPY . /opt/app/

RUN pip install -r req.txt
RUN python /opt/app/game_env/setup.py install