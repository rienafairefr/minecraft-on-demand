#!/usr/bin/env python
import time
from datetime import datetime, timedelta

import xmlrpclib
from mcstatus import MinecraftServer
from supervisor.states import ProcessStates
from supervisor.xmlrpc import SupervisorTransport

port = 25566

mcserver = MinecraftServer('localhost', port)

transport = SupervisorTransport(None, None, 'http://localhost:9001/RPC2')
transport.verbose = True

server = xmlrpclib.Server('http://unused', transport=transport)

# state machine


class PersistentState:
    wait_begin = None
    start_begin = None


persistent = PersistentState()


def server_state():
    return server.supervisor.getProcessInfo('server')['state']


def mc_no_player():
    print('no players, waiting...')
    status = mcserver.status()
    if status.players.online > 0:
        persistent.wait_begin = datetime.utcnow()
        return mc_on
    if datetime.utcnow() - persistent.wait_begin >= timedelta(seconds=10):
        server.supervisor.stopProcess('server')
        while True:
            if server_state() == ProcessStates.STOPPED:
                break
            time.sleep(1)
        return mc_off
    return mc_no_player


def mc_just_started():
    if datetime.utcnow() - persistent.start_begin >= timedelta(minutes=10):
        return mc_on
    return mc_just_started


def mc_on():
    status = mcserver.status()

    if status.players.online == 0:
        persistent.wait_begin = datetime.utcnow()
        return mc_no_player
    return mc_on


def mc_off():
    if server_state() == ProcessStates.RUNNING:
        try:
            mcserver.status()  # query the server
            persistent.start_begin = datetime.utcnow()
            return mc_just_started
        except IOError:
            return mc_off
    return mc_off


state = mc_off

while True:
    state = state()
    time.sleep(1)
