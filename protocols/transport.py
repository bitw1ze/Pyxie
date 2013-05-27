import abc
from threading import Thread


class TransportProto(metaclass=abc.ABCMeta):


    streamid = None

    def __init__(self, inbound, outbound, modifiers, db):

        self.inbound = inbound
        self.outbound = outbound
        self.modifiers = modifiers
        self.trafficdb = db
        self.streamid = db.add_stream(self)

    @abc.abstractmethod   
    def forward_outbound(self):

        return

    @abc.abstractmethod   
    def forward_inbound(self):

        return

    def start(self):

        Thread(target=self.forward_outbound).start()
        Thread(target=self.forward_inbound).start()

    @abc.abstractmethod
    def stop(self):
        return


    def call_modifiers(self, data):
        modified = data
        for m in self.modifiers:
            modified = m.modify(modified)
        return modified
