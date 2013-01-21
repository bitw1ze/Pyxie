#!/usr/bin/evn python

"""
*** intercept.py *** 

This script should be used in conjunction with the hooked version of
pidgin. It should be invoked from the python interactive interpreter.

Example:

$ python
>>> from intercept import *

# Create a Intercept object on port 8081 (default)
>>> server = Intercept(port=8081) 

# Set the mode, either manual or auto.
# Manual makes the server look for the /needle/ in the packet, saves the
# data in <Intercept instance>.data, pauses the server, and hands off
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

import socket, sys, time
from threading import Thread

class Intercept:
  NOMODE = 0
  AUTO = 1
  MANUAL = 2

  def __init__(self, port=8081):
    self.port = port
    self.mode = Intercept.NOMODE
  
  def auto(self, callback):
    self.mode = Intercept.AUTO
    self.callback = callback

  def manual(self, needle="foobar"):
    self.mode = Intercept.MANUAL
    self.needle = needle

  def nomode(self):
    self.mode = Intercept.NOMODE

  # start the server
  def start(self):
    if (self.mode == Intercept.NOMODE):
      print '[*] No interception mode is set (data will not be modified).'
      print '[*] Set mode with auto(callback) or manual(needle).'
    print '[+] Starting server'

    self.thr = Thread(target=self.run)
    self.thr.start()

  # stop the server
  def stop(self):
    self.running = False
    self.conn.close()
    self.sock.close()

  # run the server
  def run(self):
    self.running = True
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.bind(("127.0.0.1", self.port))
    self.sock.listen(1)

    while self.running:
      try:
        self.conn, self.addr = self.sock.accept()

        # FIXME
        self.data = self.conn.recv(1000000)
        self.modified = ""

        print "%s [recv]: %s" % (time.time(), self.data)

        if self.mode == Intercept.MANUAL:
          if self.data.find(self.needle) != -1:
            print '[+] intercepted data: call unpause(modified) to continue'
            self.pause()
        elif self.mode == Intercept.AUTO:
          self.modified = self.callback(self.data)

        self.conn.send(self.modified if self.modified != ""  else self.data)
        self.conn.close()
      except Exception as e:
        print '[-] exception'
        print e.message
        if self.conn:
          self.conn.close()
        self.stop()

    self.sock.close()
    print '[-] server terminated'

  def pause(self):
    self.paused = True
    while self.paused:
      pass

  def unpause(self, modified=""):
    self.modified = modified
    self.paused = False
  
def main():
  server = Intercept()
  server.auto(foobalicious)
  server.start()

def foobalicious(data):
  return data.replace("foobar", "barfoo")

if __name__ == "__main__":
  sys.exit(main())
