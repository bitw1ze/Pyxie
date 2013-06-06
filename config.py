from wrappers import SSLWrapper
wrapper = SSLWrapper

from protocols.http import HTTPProto
protocol = HTTPProto

modifiers = []

config = {
        'bind_host'     :       '',
        'bind_port'     :       443,
        'protocol'      :       HTTPProto,
        'wrapper'       :       SSLWrapper,
        'real_addr'     :       'www.facebook.com',
        'real_port'     :       443,
        'modifiers'     :       modifiers,
        'logfile'       :       '/tmp/pyxie.:TS:.log',
        'dbfile'        :       '/tmp/pyxie.:TS:.db'
        }
