from protocols.tcp import TCPProto


class HTTPProto(TCPProto):
    

    proto_name = 'http'

    def __init__(self, client, server, config):
        TCPProto.__init__(self, client, server, config)

    def forward_inbound(self):

        TCPProto.forward_inbound(self)

    def forward_outbound(self):

        TCPProto.forward_outbound(self)

class HTTPRequest:

    verb = {
            "method" : "", 
            "path" : "", 
            "params" : [],
            "version" : ""
            }
    headers = []
    body = []

class HTTPResponse:

    status = ""
    headers = []
    body = []
