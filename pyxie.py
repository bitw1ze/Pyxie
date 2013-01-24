#!/usr/bin/evn python

import socket, sys, time, struct, traceback, re, threading

class Pyxie:
    # TODO: Taken from mallory. Replace with own code or give credit in release.
  def getrealdest(self, csock):   
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

  def __init__(self, port=20755):
    self.port = port
    self.logfile = "pyxie.log"
    self.connections = []
  
  # start the server
  def start(self):
    """
    if (self.mode == Modifier.NOMODE):
      print '[*] No interception mode is set (data will not be modified).'
      print '[*] Set mode with auto(callback) or manual(needle).'
    """
    
    Pyxie.startTime = time.time()
    self.logfd = open(self.logfile, "a")
    self.startTime = time.time()
    threading.Thread(target=self.acceptConnections).start()

  # stop the server
  def stop(self):
    self.running = False
    try:
      self.proxy.close()
      self.logfd.close()
      for conn in self.connections:
        conn.stop()
    except:
      pass
    
    print '[-] stopped server'

    # run the server
  def acceptConnections(self):
    print '[+] Starting server'
    self.running = True
    self.proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.proxy.bind(('', self.port))
    self.proxy.listen(1)

    while self.running == True:
      try:
        print '[*] Waiting for connections...'
        ssock, saddr = self.proxy.accept()
        daddr, dport = self.getrealdest(ssock)
        dest = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print "destination = %s:%s" % (daddr, dport)
        
        try:
          dest.connect((daddr, dport))
          conn = TransportTCP(ssock, dest)
          self.connections.append(conn)
          self.running = True
          threading.Thread(target=conn.forward, args=(Transport.S2D,)).start()
          threading.Thread(target=conn.forward, args=(Transport.D2S,)).start()
        except Exception as e:
          print "[-] %s" % e
          dest.close()
          continue

      except KeyboardInterrupt:
        print 'got a keyboard interrupt!'
        self.stop()
        sys.exit(0)
      except Exception as e:
        print "[-] %s" % e
        pass
        
    self.stop()

class Modifier:
  NOMODE = 0
  CUSTOM = 1
  MANUAL = 2
  REGEX = 3

  def __init__(self):
    self.mode = Modifier.NOMODE

  def modify(self, data):
    if self.mode == Modifier.MANUAL:
      if re.match(self.searchRegex, data):
        print '[+] intercepted data: call unpause(modified) to continue'
        self.pause()
    elif self.mode == Modifier.CUSTOM:
      self.modified = self.callback(data)
    elif self.mode == Modifier.REGEX:
      self.modified = re.sub(self.searchRegex, self.replaceRegex, data)

  def custom(self, callback):
    self.mode = Modifier.CUSTOM
    self.customHook = callback

  def manual(self, searchRegex):
    self.mode = Modifier.MANUAL
    self.searchRegex = searchRegex

  def nomode(self):
    self.mode = Modifier.NOMODE

  def regex(self, searchRegex, replaceRegex):
    self.mode = Modifier.REGEX
    self.searchRegex = searchRegex
    self.replaceRegex = replaceRegex

  def pause(self):
      self.paused = True
      while self.paused:
        pass

  def unpause(self, modified=""):
    self.modified = modified
    self.paused = False

class Transport:
  S2D = 1
  D2S = -1

  def __init__(self):
    self.modifiers = []

class TransportTCP(Transport):
  def __init__(self, ssock, dest):
    Transport.__init__(self)
    self.ssock = ssock
    self.dest = dest
    self.startTime = time.time()

  def forward(self, *args):
    direction = args[0]

    ssock = self.ssock
    dest = self.dest

    if direction == Transport.D2S:
      ssock = self.dest
      dest = self.ssock

    data = ' '
    while data:
      try:
        data = ssock.recv(4096)
        if not data:
          try:
            ssock.shutdown(socket.SHUT_RD)
            dest.shutdown(socket.SHUT_WR)
            self.running = False
          finally:
            return
        self.modified = data

        #Log.log(data)
        print Utils.rawAscii(data)

        # allow modifier to hook data
        for m in self.modifiers:
          m.modify(data, direction)

        try:
          dest.sendall(self.modified)
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
      self.ssock.shutdown(socket.SHUT_RDWR)
      self.dest.shutdown(socket.SHUT_RDWR)
      self.ssock.close()
      self.dest.close()
    except:
      pass
    print "Stopped %s" % self

class Log:
  def __init__(self, logfile):
    self.fd = open(logfile, 'w')
  def __enter__(self):
    return self

  def __exit(self, type, value, traceback):
    self.fd.close()

  def start(self):
    self.startTime = time.time()

  def log(self, message):
    try:
      self.fd.write("[+%.2fs recv]: %s\n" % (time.time() - self.startTime, message))
    except:
      self.startTime = time.time()
      pass
    return "[+%.2fs src]: %s\n" % (time.time() - Pyxie.startTime, message)

class Utils:
  @staticmethod
  def rawAscii(data):
    return re.sub(r'\s', ' ', re.sub(r'[^ -~]', r'.', data))

  @staticmethod
  def pretty(data):
    h = data.encode('hex')
    a = Utils.rawAscii(data)
# TODO: finish this

def main():
  server = Pyxie()
  #server.auto(foobalicious)
  server.start()

"""
def foobalicious(data):
  return data.replace("foobar", "barfoo")
"""

if __name__ == "__main__":
  sys.exit(main())
