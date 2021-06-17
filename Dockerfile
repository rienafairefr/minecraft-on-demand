FROM itzg/minecraft-server:2021.8.0

MAINTAINER rienafairefr

RUN apk update

RUN apk add --no-cache --update supervisor py3-pip py3-twisted py3-cffi libffi-dev py3-cryptography

RUN apk add nodejs-current npm

COPY src/supervisord.conf /etc/

CMD []

WORKDIR /controller

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY src/*.py ./
RUN chmod +x *.py

ENTRYPOINT ["supervisord", "--nodaemon", "--configuration", "/etc/supervisord.conf"]
