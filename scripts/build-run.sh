#!/usr/bin/env bash
docker build -t minecraft-on-demand .

docker run -d -e EULA=TRUE minecraft-on-demand

python3