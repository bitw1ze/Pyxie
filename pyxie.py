#!/usr/bin/evn python

import socket, sys, time, struct, traceback, re, threading, abc, subprocess
import ssl
from OpenSSL import SSL
#import pkg_resources
#print pkg_resources.get_distribution("pyOpenSSL").version

OUTBOUND = 1
INBOUND = -1

connections = []
modifiers = []
proxy = None
port = 20755

_running = False

def add_modifier(modifier):
  modifiers.append(modifier)

# start the server
def start():
  Log.start('pyxie.log')
  threading.Thread(target=_proxy_loop).start()

# stop the server
def stop():
  _running = False 
  try:
    proxy.shutdown(socket.SHUT_RDWR)
    proxy.close()
    [conn.stop() for conn in connections]
  except:
    pass
  
  print '[-] stopped server'

def sslify(transport):
  addr = transport.dest.getpeername()
  if addr[1] != 443:
    return

  transport.dest = SSL.Connection(SSL.Context(SSL.TLSv1_METHOD), transport.dest)
  #TODO: add support for virtual hosts
  #transport.dest.set_tlsext_host_name(server_name)
  transport.dest.set_connect_state()
  transport.dest.do_handshake()
  subject = transport.dest.get_peer_certificate().get_subject()
  commonName = subject.commonName
  subject_str = ""
  for pair in subject.get_components():
    subject_str += "/%s=%s" % (pair[0], pair[1])
  subject_str += '/'
  print subject_str

  DEVNULL = None
  try:
    DEVNULL = subprocess.DEVNULL
  except:
    import os
    DEVNULL = open(os.devnull, 'wb')

  # generate the cert
  #subprocess.call(["sh", "./gencert.sh", commonName, subject_str], stdout=DEVNULL, stderr=DEVNULL)
  subprocess.call(["sh", "./gencert.sh", commonName, subject_str])

  certfile = 'cert/newcerts/%s.pem' % commonName
  server_ctx = SSL.Context(SSL.SSLv23_METHOD)
  server_ctx.use_privatekey_file(certfile)
  server_ctx.use_certificate_file(certfile)
  server_ctx.use_certificate_chain_file(certfile)
  transport.src = SSL.Connection(server_ctx, transport.src)
  transport.src.set_accept_state()
  transport.src.do_handshake()
  #TODO: hack together support for virtual hosts via server_name TLS extension
  #server_name = transport.src.get_servername()

  #transport.dest = ssl.wrap_socket(transport.dest)
  #transport.src = ssl.wrap_socket(transport.src, server_side=True, certfile="cert/amazon.crt", keyfile="cert/amazon.key", ssl_version=ssl.PROTOCOL_SSLv23)

  #subject = transport.dest.get_peer_certificate().get_subject().commonName
  #cert = ssl.DER_cert_to_PEM_cert(transport.dest.getpeercert(True)).decode('base64')

def _call_modifiers(data):
  modified = data
  for m in modifiers:
    modified = m.modify(modified)
  return modified

# run the server
def _proxy_loop():
  _running = True
  proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  proxy.bind(('', port))
  proxy.listen(1)
  print '[+] Starting server'

  while _running == True:
    try:
      src, saddr = proxy.accept()
      daddr, dport = Utils.getrealdest(src)
      dest = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      print "destination = %s:%s" % (daddr, dport)
      
      try:
        dest.connect((daddr, dport))
        conn = TCPProto(src, dest)
        connections.append(conn)
        sslify(conn)
        threading.Thread(target=conn.forward, args=(INBOUND,)).start()
        threading.Thread(target=conn.forward, args=(OUTBOUND,)).start()
      except Exception as e:
        traceback.print_exc()
        dest.close()
        src.close()
        continue

    except KeyboardInterrupt:
      print 'got a keyboard interrupt!'
      stop()
      sys.exit(0)
    except Exception as e:
      print "[-] %s" % e
      pass
 
class TransportProto:
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def forward(self, *args):
    return

  def forward_outbound(self):
    return

  def forward_inbound(self):
    return

  @abc.abstractmethod
  def stop(self):
    return

class TCPProto(TransportProto):
  def __init__(self, src, dest):
    TransportProto.__init__(self)
    self.src = src
    self.dest = dest
    self.connections = 2

  def forward(self, *args):
    direction = args[0]

    src, dest = self.src, self.dest 
    if direction == INBOUND:
      src, dest = self.dest, self.src
      
    data = ' '
    while True:
      try:
        data = src.recv(4096)
        if not data:
          raise Exception("No data received")
      except:
        try:
          self.__running = False
          src.shutdown(socket.SHUT_RD)
          dest.shutdown(socket.SHUT_WR)
          self.connections -= 1
          if self.connections <= 0:
            src.close()
            dest.close()
        except:
          pass
        return

      modified = _call_modifiers(data)
      Log.write(Utils.raw_ascii(modified))

      try:
        dest.sendall(modified)
      except:
        self.__running = False
        return
      
  def stop(self):
    self.__running = False
    try:
      self.src.shutdown(socket.SHUT_RDWR)
      self.dest.shutdown(socket.SHUT_RDWR)
      self.src.close()
      self.dest.close()
    except:
      pass
    print "Stopped %s" % self

class Modifier:
  __metaclass__ = abc.ABCMeta

  @abc.abstractmethod
  def modify(self, data):
    return

class CustomModifier(Modifier):
  def __init__(self, callback):
    self.callback = callback

  def modify(self, data):
    return self.callback(data)

class RegexModifier(Modifier):
  def __init(self, search_re, replace_re):
    self.search_re = search_re
    self.replace_re = replace_re

  def modify(self, data):
    return re.sub(self.search_re, self.replace_re, data)

class Utils:
  @staticmethod
  def raw_ascii(data):
    return re.sub(r'\s', ' ', re.sub(r'[^ -~]', r'.', data))

# TODO: finish this
  @staticmethod
  def pretty(data):
    h = data.encode('hex')
    a = Utils.raw_ascii(data)

# TODO: Taken from mallory. Replace with own code or give credit in release.
  @staticmethod
  def getrealdest(csock):   
    """
    This method only supports linux 2.4+. 
    
    Cross platform support coming soon.
    """ 
    try:
        socket.SO_ORIGINAL_DST
    except AttributeError:
        # This is not a defined socket option
        socket.SO_ORIGINAL_DST = 80
        
    # Use the Linux specific socket option to query NetFilter
    odestdata = csock.getsockopt(socket.SOL_IP, socket.SO_ORIGINAL_DST, 16)
    
    # Unpack the first 6 bytes, which hold the destination data needed                                
    _, port, a1, a2, a3, a4 = struct.unpack("!HHBBBBxxxxxxxx", odestdata)
    address = "%d.%d.%d.%d" % (a1, a2, a3, a4)
    
    return address, port

class Log:
  start_time = None
  fd = None

  @staticmethod
  def start(filename):
    try:
      Log.fd = open(filename, "w")
      Log.start_time = time.time()
    except Exception as e:
      print e
      traceback.print_exc()

  @staticmethod
  def stop():
    Log.fd.close()
    Log.start_time = None

  @staticmethod
  def write(message):
    try:
      Log.fd.write("[+%.2fs recv]: %s\n" % (time.time() - Log.start_time, message))
    except Exception as e:
      print e
      traceback.print_exc()

class ApplicationProto(TransportProto):
  __metaclass__ = abc.ABCMeta
