FROM itzg/minecraft-server

MAINTAINER rienafairefr

RUN apk add --no-cache --update supervisor py-pip py-twisted py-cffi libffi-dev py-cryptography

COPY src/supervisord.conf /etc/

CMD []

WORKDIR /controller

COPY src/requirements.txt .

RUN pip install -r requirements.txt

COPY src/*.py ./

ENTRYPOINT ["supervisord", "--nodaemon", "--configuration", "/etc/supervisord.conf"]
