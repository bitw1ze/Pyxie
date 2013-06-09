import abc
import socket
import logging
from time import time
from threading import Thread
from queue import PriorityQueue
from threading import Lock

from records import TrafficRecord


log = logging.getLogger("pyxie")


class ClosedConnectionError(Exception):    pass


class BaseProto(metaclass=abc.ABCMeta):

    client = None
    server = None
    num_connection = None
    wrapper = None

    def __init__(self, stream_id, client, server, config, listener):

        self.stream_id = stream_id
        self.client = client
        self.server = server
        self.wrapper = config['wrapper']
        self.listener = listener
        self.num_connections = 2
        self.pause_lock = Lock()
        self.pause_lock.acquire()

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
                if self.client:
                    self.client.shutdown(socket.SHUT_RDWR)
                    self.client.close()

                if self.server:
                    self.server.shutdown(socket.SHUT_RDWR)
                    self.server.close()
            except:
                pass

    def recv(self, client, server, buflen=4096):

        try:
            self.payload = client.recv(buflen)
            if not self.payload:
                raise Exception("No data received")

            record = TrafficRecord(stream=self,
                                   timestamp=time(),
                                   direction=(1 if self.client == client else 0),
                                   payload=self.payload)
            self.listener.onTrafficReceive(record)
            self.pause()

        except Exception as e:
            client.shutdown(socket.SHUT_RD)
            server.shutdown(socket.SHUT_WR)
            self.num_connections -= 1

            if self.num_connections == 0:
                try:
                    if server:
                        server.close()
                    if client:
                        client.close()

                except:
                    pass

            raise ClosedConnectionError()

    def recv_inbound(self, buflen=4096):

        try:
            self.recv(self.server, self.client, buflen)
            
        except:
            raise ClosedConnectionError()

        
    def recv_outbound(self, buflen=4096):

        try:
            self.recv(self.client, self.server, buflen)
            
        except:
            raise ClosedConnectionError()

    def send(self, client, server):

        if not self.payload:
            return

        try:
            server.sendall(self.payload)
            self.listener.onTrafficSend(self.payload)

        except Exception as e:
            #server.shutdown(socket.SHUT_WR)
            #client.shutdown(socket.SHUT_RD)
            self.num_connections -= 1

            try:
                if self.num_connections == 0:
                    if server:
                        server.close()

                    if client:
                        client.close()

                log.debug("Close connection")

            except:
                pass

            raise ClosedConnectionError()

    def send_inbound(self):

        try:
            self.send(self.server, self.client)
        except:
            raise

    def send_outbound(self):

        try:
            self.send(self.client, self.server)
        except:
            raise

    def pause(self):

        self.pause_lock.acquire()

    def unpause(self, payload):
        
        self.payload = payload
        self.pause_lock.release()
