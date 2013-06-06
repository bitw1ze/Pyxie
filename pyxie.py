import socket
import sys
import traceback
import logging
from time import time
from threading import Thread

from utils import getrealdest
from modifier import Modifier
from protocols.base import traffic_queue


log = logging.getLogger("pyxie")

class Proxy:


    def __init__(self, config, listener):

        #self.trafficdb = None
        self.config = config
        self.proxy = None
        self.streams = []
        self.listener = listener 
        self.running = False

    def start(self):

        self.proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.proxy.bind((self.config['bind_host'], self.config['bind_port']))
        self.proxy.listen(100)
        log.debug('Pyxie started')

        Thread(target=self._output_loop).start()
        Thread(target=self._proxy_loop).start()

    def stop(self):

        self.running = False 
        try:
            self.proxy.shutdown(socket.SHUT_RDWR)
            self.proxy.close()
            for stream in self.streams:
                stream.stop()
        except:
            pass
        
        log.debug('stopped server')

    def _output_loop(self):

        while True:
            latest = traffic_queue.get()
            self.listener.onTrafficReceived(latest)
            log.debug(latest)

    def _proxy_loop(self):
        
        log.debug("Got to proxy loop")
        self.running = True

        while self.running:

            try:
                client, _ = self.proxy.accept()
                log.debug("Connected to client")
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.connect(getrealdest(client))

                # TODO: add UDP support
                stream = self.config['protocol'](client, server, self.config)
                log.debug("Initialized %s protocol" % type(stream))

                self.streams.append(stream)
                stream.start()
                self.listener.onConnectionEstablished(stream)

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
