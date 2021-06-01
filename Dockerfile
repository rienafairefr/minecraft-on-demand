FROM itzg/minecraft-server:2021.14.0

MAINTAINER rienafairefr

RUN apt-get update \
    && apt-get install -yqq supervisor python3-pip python3-twisted python3-cffi libffi-dev python3-cryptography \
    && apt-get clean

COPY src/supervisord.conf /etc/

CMD []

WORKDIR /controller

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY src/*.py ./
RUN chmod +x *.py

ENTRYPOINT ["supervisord", "--nodaemon", "--configuration", "/etc/supervisord.conf"]
