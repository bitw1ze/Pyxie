#!/usr/bin/evn python

"""
*** intercept.py *** 

This script should be used in conjunction with the hooked version of
pidgin. It should be invoked from the python interactive interpreter.

Example:

$ python
>>> from intercept import *

# Create a Pyxie object on port 8081 (default)
>>> server = Pyxie(port=8081) 

# Set the mode, either manual or auto.
# Manual makes the server look for the /needle/ in the packet, saves the
# data in <Pyxie instance>.data, pauses the server, and hands off
# control to the user (you).
>>> server.manual('foobar')
# Start the server
>>> server.start()

# lots of data output to console
# ...
# <server intercepts a packet with 'foobar' in it
[+] intercepted data: call unpause(modified) to continue

# Pass unpause() the modified data you want to send.
>>> server.unpause(server.data.replace('foobar', 'barfoo'))

# Change the mode to 'auto' just for fun. But first, create a function
# that modifies traffic.

>>> def foobalicious(data):
...   return data.replace('foobar', 'barfoo')
...

# Now change the mode to auto. All traffic will be passed to
# foobalicious(), which returns the modified data back to the caller.
>>> server.auto(foobalicious)

# more data in console
# ...

# turn off interception
>>> server.nomode()

# Stop the server when we're done.
>>> server.stop()

"""

import socket, sys, time, struct
from threading import Thread

class Pyxie:
  NOMODE = 0
  AUTO = 1
  MANUAL = 2

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
    self.mode = Pyxie.NOMODE
    self.logfile = "pyxie.log"
    self.csockections = []
    self.r = self.replace
    self.ra = self.replaceAll
  
  def auto(self, callback):
    self.mode = Pyxie.AUTO
    self.callback = callback

  def manual(self, needle="foobar"):
    self.mode = Pyxie.MANUAL
    self.needle = needle

  def nomode(self):
    self.mode = Pyxie.NOMODE

  # start the server
  def start(self):
    if (self.mode == Pyxie.NOMODE):
      print '[*] No interception mode is set (data will not be modified).'
      print '[*] Set mode with auto(callback) or manual(needle).'
    print '[+] Starting server'

    self.logfd = open(self.logfile, "a")
    self.startTime = time.time()
    self.thr = Thread(target=self.handleConnection)
    self.thr.start()

  # stop the server
  def stop(self):
    self.running = False
    try:
      self.csock.close()
      self.ssock.close()
      self.dsock.close()
      self.logfd.close()
    except:
      pass

  # run the server
  def handleConnection(self):
    self.running = True
    self.ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.ssock.bind(('', self.port))
    self.ssock.listen(1)
    self.dsock = None

# TODO: move main loop to another method. spawn a thread for each connection.
# don't close connection until it is closed by the source or destination
    while self.running == True:
      try:
        self.csock, self.addr = self.ssock.accept()

        daddr, dport = self.getrealdest(self.csock)
        print "destination = %s:%s" % (daddr, dport)
        
        try:
          self.dsock = socket.connect((daddr, dport))
        except:
          self.stop()
          return

        # FIXME
        self.data = self.csock.recv(65535)
        self.modified = ""

        self.logfd.write("[+%.2fs recv]: %s\n" % (time.time() - self.startTime, self.data))

        if self.mode == Pyxie.MANUAL:
          if self.data.find(self.needle) != -1:
            print '[+] intercepted data: call unpause(modified) to continue'
            self.pause()
        elif self.mode == Pyxie.AUTO:
          self.modified = self.callback(self.data)

        self.dsock.send(self.modified if self.modified != "" else self.data)

# TODO: receive response from server and forward to the client
        self.csock.close()
      except Exception as e:
        print '[-] exception'
        print e.message
        self.stop()

    self.stop()
    print '[-] server terminated'

  def pause(self):
    self.paused = True
    while self.paused:
      pass

  def unpause(self, modified=""):
    self.modified = modified
    self.paused = False

  def replace(self, needle, replacement):
    self.unpause(self.data.replace(needle, replacement))

  def replaceAll(self, replacement):
    self.unpause(replacement)

def main():
  server = Pyxie()
  server.auto(foobalicious)
  server.start()

def foobalicious(data):
  return data.replace("foobar", "barfoo")

if __name__ == "__main__":
  sys.exit(main())
