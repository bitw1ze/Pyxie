import socket
import logging
from time import time
from threading import Thread
from queue import PriorityQueue
from threading import Lock

from records import TrafficRecord
from core import DIRECTION_INBOUND, DIRECTION_OUTBOUND


log = logging.getLogger("pyxie")


class ClosedConnectionError(Exception):    pass


class BaseProto:

    client = None
    server = None
    wrapper = None

    ''' recv and send must be implemented by subclasses '''
    def recv(self, direction): pass
    def send(self, payload, direction): pass

    def __init__(self, stream_id, client, server, config, listener):

        self.stream_id = stream_id
        self.client = client
        self.server = server
        self.wrapper = config['wrapper']
        self.listener = listener
        self.pause_lock = Lock()
        self.pause_lock.acquire()

        if self.wrapper:
            self.wrapper.wrap(self)
            log.debug("Wrapped proto with %s" % self.wrapper)

    def forward(self, direction):

        while True:
            
            try:
                payload = self.recv(direction)
                record = TrafficRecord(stream=self,
                                       timestamp=time(),
                                       direction=(direction),
                                       payload=payload)
                self.listener.onTrafficReceive(record)
                self.pause()

                #new_payload = self.listener.onTrafficReceive(record)
                #self.pause()
                #self.send_outbound(new_payload)

            except ClosedConnectionError as e:
                return

    def start(self):

        Thread(target=self.forward, args=(DIRECTION_OUTBOUND,)).start()
        Thread(target=self.forward, args=(DIRECTION_INBOUND,)).start()

    def stop(self):

        try:
            if wrapper:
                wrapper.unwrap(self)

            else:
                if self.client:
                    self.client.shutdown(socket.SHUT_RDWR)
                    self.client.close()

                if self.server:
                    self.server.shutdown(socket.SHUT_RDWR)
                    self.server.close()

            log.debug("Closed connection")

        except:
            pass

    def pause(self):

        self.pause_lock.acquire()

    def unpause(self):
        
        self.pause_lock.release()
