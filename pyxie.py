import socket
import sys
import traceback
import logging
from time import time
from threading import Thread

import config
from utils import getrealdest
from modifier import Modifier
from protocols.base import traffic_queue


log = None
trafficdb = None
proxy = None
streams = []
timestamp = str(int(time()))
pyxie_listener = None
running = False

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

def start(listener):

    global log, trafficdb, pyxie_listener, running

    logfile, dbfile= map(lambda x: x.replace("^:TS:^", timestamp),
                        (config.logfile, config.dbfile))
    pyxie_listener = listener

    log = init_logger(filename=logfile, level=logging.DEBUG)
    #trafficdb = TrafficDB(filename=dbfile)

    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy.bind(config.bindaddress)
    proxy.listen(100)
    log.debug('Pyxie started')
    Thread(target=output_loop).start()
    running = True

    Thread(target=_proxy_loop, args=(proxy))

def stop():
    running = False 
    try:
        proxy.shutdown(socket.SHUT_RDWR)
        proxy.close()
        for stream in streams:
            stream.stop()
    except:
        pass
    
    log.debug('stopped server')

def output_loop():
    while True:
        latest = traffic_queue.get()
        pyxie_listener.onTrafficReceived(latest)
        log.debug(latest)

# run the server
def _proxy_loop(args):
    
    proxy = args[0]

    while running == True:
        try:
            client, _ = proxy.accept()
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect(getrealdest(client))

            # TODO: add UDP support
            stream = config.protocol(client, server, config)
            log.debug("Initialized %s protocol" % type(stream))

            streams.append(stream)
            stream.start()

            try:
                log.info("destination = %s:%s" % stream.server.getpeername())
                log.info("source = %s:%s" % stream.client.getpeername())
            except:
                pass

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
