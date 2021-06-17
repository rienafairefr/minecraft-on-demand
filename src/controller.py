#!/usr/bin/env python3
import os
import time
from datetime import datetime, timedelta

import xmlrpc.client as xmlrpclib
from mcstatus import MinecraftServer
from supervisor.states import ProcessStates
from supervisor.xmlrpc import SupervisorTransport
import parsedatetime

port = 25566

mcserver = MinecraftServer('localhost', port)

transport = SupervisorTransport(None, None, 'http://localhost:9001/RPC2')
transport.verbose = True

server = xmlrpclib.Server('http://unused', transport=transport)

cal = parsedatetime.Calendar()
GRACE_PERIOD = cal.parseDT(os.environ.get('GRACE_PERIOD', '10 minutes'), sourceTime=datetime.min)[0] - datetime.min
print(GRACE_PERIOD)

# state machine


class PersistentState:
    wait_begin = None
    start_begin = None


persistent = PersistentState()


def get_state(process):
    return server.supervisor.getProcessInfo(process)['state']


def mc_no_player():
    status = mcserver.status()
    if status.players.online > 0:
        persistent.wait_begin = datetime.utcnow()
        print('MC-NO-PLAYER => MC-ON')
        return mc_on
    if datetime.utcnow() - persistent.wait_begin >= GRACE_PERIOD:
        server.supervisor.stopProcess('server')
        print('waiting for server to stop...')
        while True:
            if get_state('server') == ProcessStates.STOPPED:
                break
            time.sleep(1)
        print('MC-NO-PLAYER => MC-OFF')
        return mc_off
    time.sleep((GRACE_PERIOD/20).total_seconds())
    return mc_no_player


def mc_just_started():
    if datetime.utcnow() - persistent.start_begin >= timedelta(seconds=10):
        print('MC-JUST-STARTED => MC-ON')
        return mc_on
    return mc_just_started


def mc_on():
    status = mcserver.status()

    if status.players.online == 0:
        persistent.wait_begin = datetime.utcnow()
        print('ON => NO-PLAYER')
        return mc_no_player
    return mc_on


def all_off():
    if get_state('wakeup') == ProcessStates.STOPPED:
        print('starting wakeup...')
        server.supervisor.startProcess('wakeup')
        return all_off
    if get_state('wakeup') == ProcessStates.RUNNING:
        print('ALL-OFF => MC-OFF')
        return mc_off
    time.sleep(1)
    return all_off


def mc_off():
    if get_state('server') == ProcessStates.RUNNING:
        try:
            mcserver.status()  # query the server
            persistent.start_begin = datetime.utcnow()
            print('MC-OFF => MC-JUST-STARTED')
            return mc_just_started
        except IOError:
            return mc_off
    return mc_off


state = all_off

while True:
    state = state()
    time.sleep(1)
