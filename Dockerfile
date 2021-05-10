FROM itzg/minecraft-server

MAINTAINER rienafairefr

RUN apk add --no-cache --update supervisor py3-pip py3-twisted py3-cffi libffi-dev py3-cryptography

COPY src/supervisord.conf /etc/

CMD []

WORKDIR /controller

COPY src/requirements.txt .

RUN pip3 install -r requirements.txt

COPY src/*.py ./

ENTRYPOINT ["supervisord", "--nodaemon", "--configuration", "/etc/supervisord.conf"]
