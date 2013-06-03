from protocols.base import BaseProto, ClosedConnectionError


class TCPProto(BaseProto):


    proto_name = "tcp"

    def __init__(self, client, server, config):

        BaseProto.__init__(self, client, server, config)

    def forward_outbound(self):
        while True:
            
            try:
                data = self.recv_outbound()
                self.send_outbound(data)

            except ClosedConnectionError as e:
                return

    def forward_inbound(self):

        while True:

            try:
                data = self.recv_inbound()
                self.send_inbound(data)

            except ClosedConnectionError as e:
                return
