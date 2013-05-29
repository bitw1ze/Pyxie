import abc
import socket
import logging
from threading import Thread


log = logging.getLogger("pyxie")


class ClosedConnectionError(Exception):
    pass


class TransportProto(metaclass=abc.ABCMeta):

    client = None
    server = None
    modifiers = None
    trafficdb = None
    streamid = None
    num_connection = None
    wrapper = None

    def __init__(self, client, server, modifiers, db, wrapper):

        self.client = client
        self.server = server
        self.modifiers = modifiers
        self.trafficdb = db
        self.streamid = db.add_stream(self)
        self.wrapper = wrapper
        self.num_connections = 2

        if wrapper:
            wrapper.wrap(self)
            log.debug("Wrapped proto with %s" % wrapper)

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
                raise

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
            self.num_connections -= 1

            if self.num_connections == 0:
                if server:
                    server.close()
                if client:
                    client.close()

            raise ClosedConnectionError()

    def recv_inbound(self):
        
        try:
            data = self.recv(self.server, self.client)
            Thread(
                    target=self.trafficdb.add_traffic,
                    args=(self, False, False, data)
            ).start()
            return data
        except:
            raise

    def recv_outbound(self):

        try:
            data = self.recv(self.client, self.server)
            Thread(
                    target=self.trafficdb.add_traffic,
                    args=(self, True, False, data)
            ).start()
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
