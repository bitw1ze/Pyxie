from protocols.tcp import TCPProto

class HTTPProto(TCPProto):
    

    def __init__(self, inbound, outbound):

        TCPProto.__init__(self, inbound, outbound)

    def forward_inbound(self):
        TCPProto.forward_inbound(self)

        pass

    def forward_outbound(self):
        TCPProto.forward_outbound(self)

        pass
