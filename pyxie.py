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
    if (self.mode == TcpTransport.NOMODE):
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
      self.psock.close()
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
    self.psock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.psock.bind(('', self.port))
    self.psock.listen(1)

    while self.running == True:
      try:
        print '[*] Waiting for connections...'
        ssock, saddr = self.psock.accept()
        daddr, dport = self.getrealdest(ssock)
        dsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print "destination = %s:%s" % (daddr, dport)
        
        try:
          dsock.connect((daddr, dport))
          conn = TcpTransport(ssock, dsock)
          self.connections.append(conn)
          self.running = True
          threading.Thread(target=conn.forward, args=(TcpTransport.S2D,)).start()
          threading.Thread(target=conn.forward, args=(TcpTransport.D2S,)).start()
        except Exception as e:
          print "[-] %s" % e
          dsock.close()
          continue

      except KeyboardInterrupt:
        print 'got a keyboard interrupt!'
        self.stop()
        sys.exit(0)
      except Exception as e:
        print "[-] %s" % e
        pass
        
    self.stop()

  
class TcpTransport:
  NOMODE = 0
  AUTO = 1
  MANUAL = 2

  S2D = 1
  D2S = -1

  def __init__(self, ssock, dsock):
    self.ssock = ssock
    self.dsock = dsock
    self.startTime = time.time()
    self.mode = TcpTransport.NOMODE
    #self.r = self.replace
    #self.ra = self.replaceAll

  def rawAscii(self, data):
    return re.sub(r'\s', ' ', re.sub(r'[^ -~]', r'.', data))
  
  def log(self, message):
    #self.logfd.write("[+%.2fs recv]: %s\n" % (time.time() - self.startTime, data))
    return "[+%.2fs src]: %s\n" % (time.time() - Pyxie.startTime, message)

  def forward(self, *args):
    direction = args[0]

    ssock = self.ssock
    dsock = self.dsock

    if direction == TcpTransport.D2S:
      ssock = self.dsock
      dsock = self.ssock

    data = ' '
    while data:
      try:
        data = ssock.recv(8192)
        if not data:
          try:
            ssock.shutdown(socket.SHUT_RD)
            dsock.shutdown(socket.SHUT_WR)
            self.running = False
          finally:
            return
        self.modified = data

        self.log(data)
        print self.rawAscii(data)

        if self.mode == TcpTransport.MANUAL:
          if data.find(self.needle) != -1:
            print '[+] intercepted data: call unpause(modified) to continue'
            self.pause()
        elif self.mode == TcpTransport.AUTO:
          self.modified = self.callback(data)

        try:
          dsock.sendall(self.modified)
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

  """
  def auto(self, callback):
    self.mode = TcpTransport.AUTO
    self.callback = callback

  def manual(self, needle="foobar"):
    self.mode = TcpTransport.MANUAL
    self.needle = needle

  def nomode(self):
    self.mode = TcpTransport.NOMODE

  def pause(self):
      self.paused = True
      while self.paused:
        pass

  def unpause(self, modified=""):
    self.modified = modified
    self.paused = False

  def replace(self, needle, replacement):
    self.unpause(data.replace(needle, replacement))

  def replaceAll(self, replacement):
    self.unpause(replacement)
  """

  def stop(self):
    self.running = False
    try:
      self.ssock.shutdown(socket.SHUT_RDWR)
      self.dsock.shutdown(socket.SHUT_RDWR)
      self.ssock.close()
      self.dsock.close()
    except:
      pass
    
    print "Stopped %s" % self

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
