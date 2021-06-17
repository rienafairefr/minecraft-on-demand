FROM itzg/minecraft-server:java16

MAINTAINER rienafairefr

RUN apk update && \
    apk add --no-cache --update supervisor py3-pip py3-twisted py3-cffi libffi-dev py3-cryptography; exit 0;

RUN apt-get update
RUN apt-get install -y supervisor python3-pip 
RUN apt-get install -y python3-twisted python3-cffi libffi-dev python3-cryptography

COPY src/supervisord.conf /etc/

CMD []

WORKDIR /controller

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY src/*.py ./
RUN chmod +x *.py

ENTRYPOINT ["supervisord", "--nodaemon", "--configuration", "/etc/supervisord.conf"]
