import abc
import socket
import logging
from time import time
from threading import Thread
from queue import PriorityQueue

from records import TrafficRecord

log = logging.getLogger("pyxie")
traffic_queue = PriorityQueue()


class ClosedConnectionError(Exception):
    pass


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
            payload = client.recv(buflen)
            if not payload:
                raise Exception("No data received")

            record = TrafficRecord(stream_id=self.stream_id,
                                   timestamp=time(),
                                   direction=(1 if self.client == client else 0),
                                   payload=payload)
            self.listener.onTrafficReceive(record)

            return payload 

        except Exception as e:
            import traceback
            traceback.print_exc()
            #client.shutdown(socket.SHUT_RD)
            #server.shutdown(socket.SHUT_WR)
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
            payload = self.recv(self.server, self.client, buflen)
            
            return payload

        except:
            raise ClosedConnectionError()

        
    def recv_outbound(self, buflen=4096):

        try:
            payload = self.recv(self.client, self.server, buflen)
            
            return payload

        except:
            raise ClosedConnectionError()

    def send(self, client, server, payload):

        if not payload:
            return

        payload = self.listener.onTrafficModify(payload)

        try:
            server.sendall(payload)
            self.listener.onTrafficSend(payload)

        except:
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

    def send_inbound(self, payload):

        try:
            self.send(self.server, self.client, payload)
        except:
            raise

    def send_outbound(self, payload):

        try:
            self.send(self.client, self.server, payload)
        except:
            raise
