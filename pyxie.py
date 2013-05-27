#!/usr/bin/evn python

import socket
import sys
import traceback
import logging

import config
from utils import getrealdest
from modifier import Modifier
from trafficdb import TrafficDB

log = None
trafficdb = None
proxy = None
streams = []

_running = False

def init_logger(filename=None, level=logging.WARNING):

    """Initializes and returns a Logger object"""

    log = logging.getLogger('pyxie')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    if filename:
        fhdlr = logging.FileHandler(filename)
        fhdlr.setFormatter(formatter)
        log.addHandler(fhdlr) 

    chdlr = logging.StreamHandler()
    chdlr.setFormatter(formatter)
    log.addHandler(chdlr)
    
    log.setLevel(level)
    return log

# start the server
def start():
    global log, trafficdb
    trafficdb = TrafficDB(filename=config.dbfile)
    log = init_logger(filename=config.logfile, level=logging.DEBUG)
    _proxy_loop()

# stop the server
def stop():
    _running = False 
    try:
        proxy.shutdown(socket.SHUT_RDWR)
        proxy.close()
        for stream in streams:
            stream.stop()
    except:
        pass
    
    log.debug('stopped server')

# run the server
def _proxy_loop():
    _running = True
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.bind(config.bindaddress)
    proxy.listen(100)
    log.debug('Pyxie started')

    while _running == True:
        try:
            inbound, _ = proxy.accept()
            outbound = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            outbound.connect(getrealdest(inbound))

            # TODO: add UDP support
            stream = config.protocol(inbound, outbound, 
                                     config.modifiers, trafficdb)
            log.debug("Initialized %s protocol" % type(stream))

            if config.wrapper:
                config.wrapper.wrap(stream)
                log.debug("Wrapped proto with %s" % config.wrapper)

            streams.append(stream)
            stream.start()

            log.info("destination = %s:%s" % stream.outbound.getpeername())
            #log.info("source = %s:%s" % stream.inbound.getpeername())

        except Exception as e:
            try:
                outbound.close()
                inbound.close()
            except:
                pass

            raise

        except KeyboardInterrupt:
            log.exception('got a keyboard interrupt!')
            stop()
            sys.exit(0)
