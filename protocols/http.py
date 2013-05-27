from protocols.tcp import TCPProto
import logging

log = logging.getLogger("pyxie")

class HTTPProto(TCPProto):
    

    proto_name = 'http'

    def __init__(self, inbound, outbound, modifiers, db):
        TCPProto.__init__(self, inbound, outbound, modifiers, db)

    def forward_inbound(self):

        TCPProto.forward_inbound(self)

    def forward_outbound(self):

        TCPProto.forward_outbound(self)
