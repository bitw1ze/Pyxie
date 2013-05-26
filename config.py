bindaddress = ('', 443)

from wrappers import SSLWrapper
wrapper = SSLWrapper

from protocols.http import HTTPProto
protocol = HTTPProto

realdest = ('www.facebook.com', 443)
