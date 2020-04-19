#!/usr/bin/env python
"""
Wakeup  server

This server accepts players, then starts the real server (server process for supervisor)
"""
import logging
import xmlrpclib

from mcstatus import MinecraftServer
from quarry.net.proxy import DownstreamFactory, Bridge, Downstream
from supervisor.xmlrpc import SupervisorTransport
from twisted.internet import reactor

transport = SupervisorTransport(None, None, 'http://localhost:9001/RPC2')
transport.verbose = True


server = xmlrpclib.Server('http://unused', transport=transport)


mcserver = MinecraftServer('localhost', 25566)

state = {
    'starting': False,
    'started': False,
}


class WakeupProtocol(Downstream):
    log_level = logging.DEBUG

    def __init__(self, factory, remote_addr):
        super(WakeupProtocol, self).__init__(factory, remote_addr)

    def packet_status_request(self, buff):
        print('got a status request packet')

        if not state['starting']:
            # first packet
            server.supervisor.startProcess('server')
            state['starting'] = True
            message = 'Server is starting, please wait...'
        else:
            # subsequent packet(s)

            try:
                status = mcserver.status()
                if not state['started']:
                    message = 'Server is started: %s' % status.description['text']
                    state['started'] = True
                else:
                    message = status.description['text']
            except IOError:
                message = 'Server is not yet started, please wait...'

        self.factory.motd = message
        super(WakeupProtocol, self).packet_status_request(buff)


class WakeupFactory(DownstreamFactory):
    protocol = WakeupProtocol


def main():
    factory = WakeupFactory()
    factory.bridge_class = Bridge
    factory.connect_host = "127.0.0.1"
    factory.connect_port = 25566
    factory.online_mode = False
    factory.listen("0.0.0.0", 25565)
    reactor.run()


if __name__ == "__main__":
    import sys
    main()


