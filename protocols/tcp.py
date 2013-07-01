import logging

from protocols.base import BaseProto, ClosedConnectionError
from core import DIRECTION_INBOUND, DIRECTION_OUTBOUND


log = logging.getLogger("pyxie")


class TCPProto(BaseProto):


    proto_name = "tcp"

    def __init__(self, stream_id, client, server, config, listener):

        BaseProto.__init__(self, stream_id, client, server, config, listener)

    def recv(self, direction):

        try:
            if direction == DIRECTION_OUTBOUND:
                client, server = self.client, self.server
            elif direction == DIRECTION_INBOUND:
                client, server = self.server, self.client
            else:
                raise Exception("Invalid Direction")

            payload = client.recv(4096)
            if not payload:
                raise Exception("No data received")

            return payload

        except Exception as e:
            self.stop()
            raise ClosedConnectionError()

    def send(self, payload, direction):

        if not payload:
            return

        if direction == DIRECTION_OUTBOUND:
            client, server = self.client, self.server
        elif direction == DIRECTION_INBOUND:
            client, server = self.server, self.client
        else:
            raise Exception("Invalid Direction")

        try:
            server.sendall(payload)

        except Exception as e:
            self.stop()
            raise ClosedConnectionError()
