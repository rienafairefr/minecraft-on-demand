#!/usr/bin/env python3
"""
Wakeup  server

This server accepts players, then starts the real server (server process for supervisor)

wakeup binds to $SERVER_PORT, and the subprocess binds to 25566
"""
import sys
import traceback

import logging
import os
import time
import xmlrpc.client as xmlrpclib


from jproperties import Properties
from mcstatus import MinecraftServer
from quarry.net.proxy import DownstreamFactory, Bridge, Downstream
from supervisor.xmlrpc import SupervisorTransport
from twisted.internet import reactor

transport = SupervisorTransport(None, None, 'http://localhost:9001/RPC2')
transport.verbose = True


server = xmlrpclib.Server('http://unused', transport=transport)


starting = 'starting'
started = 'started'
stopped = 'stopped'


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


class PersistentState:
    server = stopped
    wakeup_port = int(os.environ.get('SERVER_PORT', 25565))
    server_port = 25566
    motd = os.environ.get('MOTD', 'Unknown MOTD')
    online_mode = str2bool(os.environ['ONLINE_MODE'])


state = PersistentState()

mcserver = MinecraftServer('localhost', state.server_port)


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

    def __init__(self, factory, remote_addr):
        load_properties()
        super(WakeupProtocol, self).__init__(factory, remote_addr)

    def data_received(self, data):
        try:
            return super(WakeupProtocol, self).data_received(data)
        except Exception:
            pass

    def player_joined(self):
        print('player wants to join')
        if state.server == stopped:
            # first packet

            server.supervisor.startProcess('server')
            state.server = starting
            while True:
                try:
                    mcserver.status()
                    state.server = started
                    print('Server is started, continuing...')
                    break
                except IOError:
                    print('Server is not yet started, please wait...')
                time.sleep(1)
        elif state.server == starting:
            return

        super(WakeupProtocol, self).player_joined()

    def packet_status_request(self, buff):
        print('got a status request packet')
        try:
            status = mcserver.status()
            # just in case the it can change
            state.motd = status.description['text']
        except IOError:
            pass

        if state.server != started:
            self.factory.motd = 'on-demand (%s): %s: Join to start' % (state.server, state.motd)
        else:
            self.factory.motd = state.motd

        super(WakeupProtocol, self).packet_status_request(buff)


class WakeupFactory(DownstreamFactory):
    protocol = WakeupProtocol


def main():
    print('main')
    factory = WakeupFactory()
    factory.bridge_class = Bridge
    factory.connect_host = "127.0.0.1"
    factory.connect_port = state.server_port
    factory.online_mode = state.online_mode
    factory.listen("0.0.0.0", state.wakeup_port)
    if str2bool(os.environ.get('DEBUG', 'false')):
        factory.log_level = logging.DEBUG
    reactor.run()


if __name__ == "__main__":
    main()
