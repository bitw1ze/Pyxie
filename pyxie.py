#!/usr/bin/evn python

import socket
import sys
import traceback
import logging

import config
from utils import getrealdest
from modifier import Modifier

_running = False
log = None
streams = []
modifiers = []
proxy = None

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

def add_modifier(modifier):
  modifiers.append(modifier)

# start the server
def start():
    global log
    #trafficDB = PyxieDB(filename="pyxie.sqlite")
    log = init_logger(filename="/tmp/pyxie.log", level=logging.DEBUG)
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
    
    log.info('stopped server')

def _call_modifiers(data):
    modified = data
    for m in modifiers:
        modified = m.modify(modified)
    return modified

# run the server
def _proxy_loop():
    _running = True
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.bind(config.bindaddress)
    proxy.listen(1)
    log.info('Pyxie started')

    while _running == True:
        try:
            inbound, _ = proxy.accept()
            outbound = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            outbound.connect(config.realdest)
            # TODO: outbound.connect(getrealdest(inbound))

            # TODO: add UDP support
            stream = config.protocol(inbound, outbound)
            log.debug("Initialized %s protocol" % type(stream))

            if config.wrapper:
                config.wrapper.wrap(stream)
                log.debug("Wrapped proto with %s" % config.wrapper)

            stream.start()

            streams.append(stream)
            log.info("destination = %s:%s" % stream.outbound.getpeername())
            #log.info("source = %s:%s" % stream.inbound.getpeername())

        except Exception as e:
            outbound.close()
            inbound.close()
            raise

        except KeyboardInterrupt:
            log.exception('got a keyboard interrupt!')
            stop()
            sys.exit(0)

        except Exception as e:
            traceback.print_exc()
            log.exception("[-] %s" % e)
            pass
