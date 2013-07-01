import re

from wrappers.ssl import SSLWrapper
from protocols.http import HTTPProto
from protocols.tcp import TCPProto


class MyModifier:

    def __init__(self):

        pass

    def modify(self, data):

        return re.sub(r'Accept-Encoding:.*\r\n', '', 
                data.decode('utf8', 'ignore')).encode('utf8')


wrapper = SSLWrapper
protocol = TCPProto
#protocol = HTTPProto
modifiers = [MyModifier()]

config = {
        'bind_host'     :       '',
        'bind_port'     :       443,
        'protocol'      :       protocol,
        'wrapper'       :       wrapper,
        'real_addr'     :       'www.facebook.com',
        'real_port'     :       443,
        'modifiers'     :       modifiers,
        'logfile'       :       '/tmp/pyxie.:TS:.log',
        'dbfile'        :       '/tmp/pyxie.:TS:.db'
        }
