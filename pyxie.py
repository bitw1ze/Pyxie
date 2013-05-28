import socket
import sys
import traceback
import logging
from time import time

import config
from utils import getrealdest
from modifier import Modifier
from trafficdb import TrafficDB

log = None
trafficdb = None
proxy = None
streams = []
timestamp = str(int(time()))

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

    logfile, dbfile= map(lambda x: x.replace("^:TS:^", timestamp),
                        (config.logfile, config.dbfile))

    log = init_logger(filename=logfile, level=logging.DEBUG)
    trafficdb = TrafficDB(filename=dbfile)
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
            client, _ = proxy.accept()
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect(getrealdest(client))

            # TODO: add UDP support
            stream = config.protocol(client, server, config.modifiers,
                                    trafficdb, config.wrapper)
            log.debug("Initialized %s protocol" % type(stream))

            streams.append(stream)
            stream.start()

            log.info("destination = %s:%s" % stream.server.getpeername())
            log.info("source = %s:%s" % stream.client.getpeername())

        except Exception as e:
            try:
                server.close()
                client.close()
            except:
                pass

            raise

        except KeyboardInterrupt:
            log.exception('Execution interrupted by user (ctrl+c)')
            stop()
            sys.exit(0)
