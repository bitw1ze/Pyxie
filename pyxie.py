#!/usr/bin/evn python

import socket, sys, time, struct, traceback, re, threading, abc, mutex
import ssl

OUTBOUND = 1
INBOUND = -1

connections = []
modifiers = []
proxy = None
port = 20755
running = False

def add_modifier(modifier):
  modifiers.append(modifier)

# start the server
def start():
  Log.start('pyxie.log')
  threading.Thread(target=_proxy_loop).start()

# stop the server
def stop():
  try:
    proxy.shutdown(socket.SHUT_RDWR)
    proxy.close()
    [conn.stop() for conn in connections]
  except:
    pass
  
  print '[-] stopped server'

def sslify(transport):
  socket
  if transport.dest.getpeername()[1] == 443:
    transport.src = ssl.wrap_socket(transport.src, server_side=True, certfile="cert.pem", keyfile="cert.pem", ssl_version=ssl.PROTOCOL_SSLv23)
    transport.dest = ssl.wrap_socket(transport.dest)

def _call_modifiers(data):
  modified = data
  for m in modifiers:
    modified = m.modify(modified)
  return modified

# run the server
def _proxy_loop():
  running = True
  proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  proxy.bind(('', port))
  proxy.listen(1)
  print '[+] Starting server'

  while running == True:
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
        running = True
        threading.Thread(target=conn.forward, args=(OUTBOUND,)).start()
        threading.Thread(target=conn.forward, args=(INBOUND,)).start()
      except Exception as e:
        print "[-] %s" % e
        dest.close()
        continue

    except KeyboardInterrupt:
      print 'got a keyboard interrupt!'
      stop()
      sys.exit(0)
    except Exception as e:
      print "[-] %s" % e
      pass

"""
class SSLProto(ApplicationProto):
  def __init__(self):
    self.handshake_complete = False
    
  @staticmethod
  def match(sock, data):
    return sock.getpeername().split(':')[1] == "443"
"""
  
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

  def forward(self, *args):
    direction = args[0]

    src = self.src
    dest = self.dest

    if direction == INBOUND:
      src = self.dest
      dest = self.src

    data = ' '
    while True:
      try:
        data = src.recv(8192)
        if not data:
          try:
            src.shutdown(socket.SHUT_RD)
            dest.shutdown(socket.SHUT_WR)
            self.running = False
          finally:
            return

        Log.write(Utils.raw_ascii(data))

        modified = _call_modifiers(data)

        try:
          dest.sendall(modified)
        except:
          self.running = False
                
      except KeyboardInterrupt:
        print 'keyboard interrupt'
        self.stop()
        return

      except Exception as e:
        print "[-] %s" % e
        traceback.print_exc()
        return

  def stop(self):
    self.running = False
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
