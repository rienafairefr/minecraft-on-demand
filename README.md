Docker Hub: [![](https://images.microbadger.com/badges/version/rienafairefr/minecraft-on-demand.svg)](https://hub.docker.com/r/rienafairefr/minecraft-on-demand) [![](https://images.microbadger.com/badges/image/rienafairefr/minecraft-on-demand.svg)](https://hub.docker.com/r/rienafairefr/minecraft-on-demand)

A Docker image, based on tzg/minecraft-server, that will auto-start and auto-stop depending on 
users trying to connect to it or connected to it.

This might be useful for cases where you don't want to keep resources (CPU, memory) tied to
a running minecraft server if you're not using it. Supporting multiple worlds on a single host
that could not handle all of them running at the same time, etc.

There might be a better way to do it, but I did it that way:

- Processes inside the docker container are managed by supervisor
- There is a "wakeup" process that is binding to the port $SERVER_PORT, usually 25565 (default Minecraft Server port).
- "wakeup" runs a simple Proxy Minecraft server (using a `quarry` Bridge) which listens for players wanting
to join the server.
If the server is down, then the server process is started. 
- When the server gets empty (monitored through `mcstatus` ), after some time then the server process is stopped

Caveats: 

- first startup could be long enough that the first player to join times out 
- the server subprocess listens on hardcoded port 25566

