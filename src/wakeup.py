#!/usr/bin/env python3
"""
Wakeup  server

This server accepts players, then starts the real server (server process for supervisor)

wakeup binds to $SERVER_PORT, and the subprocess binds to 25566
"""
import argparse
import logging
import os
import sys
import time
import xmlrpc.client as xmlrpclib
from dataclasses import dataclass, asdict
from pprint import pprint

from jproperties import Properties
from mcstatus import MinecraftServer
from quarry.net.proxy import DownstreamFactory, Bridge, Downstream
from supervisor.xmlrpc import SupervisorTransport
from twisted.internet import reactor, defer

transport = SupervisorTransport(None, None, 'http://localhost:9001/RPC2')
transport.verbose = True

server = xmlrpclib.Server('http://unused', transport=transport)

starting = 'starting'
started = 'started'
stopped = 'stopped'

STOPPED = 0
STARTING = 10
RUNNING = 20
BACKOFF = 30
STOPPING = 40
EXITED = 100
FATAL = 200
UNKNOWN = 1000


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


@dataclass
class PersistentState:
    motd: str = os.environ.get('MOTD', 'Unknown MOTD')


state = PersistentState()
pprint(asdict(state))


def load_properties():
    # if the server has already been created,
    # then it can read server.properties to get the motd
    p = Properties()

    try:
        with open("/data/server.properties", "rb") as f:
            p.load(f)

        state.motd = p['motd'].data
    except:
        pass


class WakeupProtocol(Downstream):
    log_level = logging.DEBUG

    def __init__(self, factory, remote_addr, mcserver):
        load_properties()
        self.mcserver = mcserver
        super(WakeupProtocol, self).__init__(factory, remote_addr)

    def data_received(self, data):
        try:
            return super(WakeupProtocol, self).data_received(data)
        except Exception:
            pass

    def player_joined(self):
        print('player wants to join')

        try:
            self.mcserver.status()
            print('Server is started, continuing...')
        except:
            server_state = server.supervisor.getProcessInfo('server')['state']
            print('server_state')
            print(server_state)
            if server_state == STOPPED:
                # first packet

                server.supervisor.startProcess('server')
                while True:
                    try:
                        self.mcserver.status()
                        print('Server is started, continuing...')
                        break
                    except IOError:
                        print('Server is not yet started, please wait...')
                    time.sleep(1)
            elif server_state == STARTING:
                return

        super(WakeupProtocol, self).player_joined()

    def packet_status_request(self, buff):
        print('got a status request packet')
        try:
            status = self.mcserver.status()
            # just in case the it can change
            state.motd = status.description['text']
        except IOError:
            pass

        server_state = server.supervisor.getProcessInfo('server')['state']
        if server_state != RUNNING:
            self.factory.motd = f'on-demand (Stopped): {state.motd}: Join to start'
        else:
            self.factory.motd = state.motd

        super(WakeupProtocol, self).packet_status_request(buff)


class WakeupDownstreamFactory(DownstreamFactory):
    protocol = WakeupProtocol

    def __init__(self, mcserver):
        super().__init__()
        self.mcserver = mcserver

    def buildProtocol(self, addr):
        return self.protocol(self, addr, self.mcserver)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen-host", default="", help="address to listen on")
    parser.add_argument("--listen-port", default=25565, type=int, help="port to listen on")
    parser.add_argument("--connect-host", help="address to connect to")
    parser.add_argument("--connect-port", type=int, help="port to connect to")
    parser.add_argument("--online-mode", action='store_true')
    args = parser.parse_args(argv)

    mcserver = MinecraftServer(args.connect_host, args.connect_port)

    factory = WakeupDownstreamFactory(mcserver)
    factory.connect_host = args.connect_host
    factory.connect_port = args.connect_port
    online_mode: bool = str2bool(os.environ.get('ONLINE_MODE', 'TRUE'))
    if args.online_mode:
        online_mode = True

    print('online mode' if online_mode else 'offline mode')
    factory.online_mode = online_mode
    factory.listen(args.listen_host, args.listen_port)
    if str2bool(os.environ.get('DEBUG', 'false')):
        factory.log_level = logging.DEBUG


if __name__ == "__main__":
    main(sys.argv[1:])
    reactor.run()
