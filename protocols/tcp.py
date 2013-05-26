import socket
import logging

from protocols.transport import TransportProto

log = logging.getLogger("pyxie")

class TCPProto(TransportProto):


    def __init__(self, inbound, outbound):

        TransportProto.__init__(self, inbound, outbound)

    def forward_outbound(self):

        return self.forward(self.inbound, self.outbound)

    def forward_inbound(self):

        return self.forward(self.outbound, self.inbound)

    def forward(self, inbound, outbound):

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

            #modified = _call_modifiers(data)
            # TODO: send to logger
            #print(Utils.printable_ascii(modified))
            #print(Utils.dump_asciihex(data))
            modified = data

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
