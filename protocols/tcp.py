import socket
import logging

from protocols.transport import TransportProto

log = logging.getLogger("pyxie")

class TCPProto(TransportProto):


    proto_name = "tcp"

    def __init__(self, inbound, outbound, modifiers, db):

        TransportProto.__init__(self, inbound, outbound, modifiers, db)

    def forward_outbound(self):

        inbound, outbound = self.inbound, self.outbound

        data = ' '
        while True:
            try:
                data = inbound.recv(1024)
                log.debug(data)
                if not data:
                    raise Exception("No data received")
            except:
                self.__running = False
                try:
                    inbound.shutdown(socket.SHUT_RD)
                    outbound.shutdown(socket.SHUT_WR)
                    inbound.close()
                    outbound.close
                except:
                    pass
                return

            modified = self.call_modifiers(data)
            self.trafficdb.add_traffic(self, self.streamid, 1, 0, modified)

            try:
                outbound.sendall(modified)
            except:
                self.__running = False
                return

    def forward_inbound(self):

        inbound, outbound = self.outbound, self.inbound

        data = ' '
        while True:
            try:
                data = inbound.recv(1024)
                log.debug(data)
                if not data:
                    raise Exception("No data received")
            except:
                self.__running = False
                try:
                    inbound.shutdown(socket.SHUT_RD)
                    outbound.shutdown(socket.SHUT_WR)
                    inbound.close()
                    outbound.close
                except:
                    pass
                return

            modified = self.call_modifiers(data)
            self.trafficdb.add_traffic(self, self.streamid, 0, 0, modified)

            try:
                outbound.sendall(modified)
            except:
                self.__running = False
                return

                    
    def stop(self):
        self.__running = False
        try:
            self.inbound.shutdown(socket.SHUT_RDWR)
            self.outbound.shutdown(socket.SHUT_RDWR)
            self.inbound.close()
            self.outbound.close()
        except:
            pass
        print("Stopped %s" % self)

