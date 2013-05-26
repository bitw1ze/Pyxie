from protocols.tcp import TCPProto
import logging

log = logging.getLogger("pyxie")

class HTTPProto(TCPProto):
    

    def __init__(self, inbound, outbound, modifiers):
        TCPProto.__init__(self, inbound, outbound, modifiers)
        log.debug(self.modifiers)

    def forward_inbound(self):

        TCPProto.forward_inbound(self)

    def forward_outbound(self):

        TCPProto.forward_outbound(self)
