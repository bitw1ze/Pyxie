from protocols.tcp import TCPProto


class HTTPProto(TCPProto):
    

    proto_name = 'http'

    def __init__(self, stream_id, client, server, config, listener):

        TCPProto.__init__(self, stream_id, client, server, config, listener)


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
