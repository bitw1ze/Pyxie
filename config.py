# bindaddress: tuple containing address of interface and port to bind proxy 
bindaddress = ('', 443)

from wrappers import SSLWrapper
wrapper = SSLWrapper

from protocols.http import HTTPProto
protocol = HTTPProto

realdest = ('www.facebook.com', 443)

modifiers = []

logfile = '/tmp/pyxie.:TS:.log'
dsn = "dbname=pyxie user=pyxie"
