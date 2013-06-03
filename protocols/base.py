import abc
import socket
import logging
from time import time
from threading import Thread
from queue import PriorityQueue

log = logging.getLogger("pyxie")
traffic_queue = PriorityQueue()


class ClosedConnectionError(Exception):
    pass


class BaseProto(metaclass=abc.ABCMeta):

    client = None
    server = None
    modifiers = None
    num_connection = None
    wrapper = None

    def __init__(self, client, server, config):

        self.client = client
        self.server = server
        self.modifiers = config.modifiers
        self.wrapper = config.wrapper
        self.num_connections = 2

        if self.wrapper:
            self.wrapper.wrap(self)
            log.debug("Wrapped proto with %s" % self.wrapper)

    @abc.abstractmethod   
    def forward_outbound(self):

        return

    @abc.abstractmethod   
    def forward_inbound(self):

        return

    def start(self):

        Thread(target=self.forward_outbound).start()
        Thread(target=self.forward_inbound).start()

    def stop(self):

        if wrapper:
            wrapper.unwrap(self)

        else:
            try:
                self.client.shutdown(socket.SHUT_RDWR)
                self.server.shutdown(socket.SHUT_RDWR)
                self.client.close()
                self.server.close()
            except:
                pass

    def call_modifiers(self, data):
        modified = data
        for m in self.modifiers:
            modified = m.modify(modified)
        return modified

    def recv(self, client, server):

        try:
            data = client.recv(4096)

            if not data:
                raise Exception("No data received")

            return data

        except:
            #client.shutdown(socket.SHUT_RD)
            #server.shutdown(socket.SHUT_WR)
            self.num_connections -= 1

            if self.num_connections == 0:
                server.close()
                client.close()

            raise ClosedConnectionError()

    def recv_inbound(self):
        
        try:
            data = self.recv(self.server, self.client)
            traffic_queue.put((time(), (self, 0, 0, data)))
            return data
        except:
            raise

    def recv_outbound(self):

        try:
            data = self.recv(self.client, self.server)
            traffic_queue.put((time(), (self, 1, 0, data)))
            return data

        except:
            raise

    def send(self, client, server, data):

        modified = self.call_modifiers(data)

        try:
            server.sendall(modified)

        except:
            #server.shutdown(socket.SHUT_WR)
            #client.shutdown(socket.SHUT_RD)
            self.num_connections -= 1

            if self.num_connections == 0:
                server.close()
                client.close()
            log.debug("Close connection")

            raise ClosedConnectionError()

    def send_inbound(self, data):

        try:
            self.send(self.server, self.client, data)
        except:
            raise

    def send_outbound(self, data):

        try:
            self.send(self.client, self.server, data)
        except:
            raise
