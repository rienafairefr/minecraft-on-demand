FROM itzg/minecraft-server

RUN apk add --no-cache --update supervisor py-pip py-twisted py-cffi libffi-dev py-cryptography

COPY src/supervisord.conf /etc/

CMD []

WORKDIR /controller

COPY src/requirements.txt .

RUN pip install -r requirements.txt

COPY src/*.py ./

ENV SERVER_PORT 25566

ENTRYPOINT ["supervisord", "--nodaemon", "--configuration", "/etc/supervisord.conf"]
