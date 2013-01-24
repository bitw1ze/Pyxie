import pyxie, sys

def mod(data):
  if data.find("foobar"):
    pyxie.Log.write("changed foobar to barfoo!")
  return data.replace('foobar', 'barfoo')

def main():
  try:
    pyxie.add_modifier(pyxie.CustomModifier(mod))
    pyxie.start()
  except KeyboardInterrupt as e:
    print e
    pyxie.stop()
    sys.exit(0)
  #server.auto(foobalicious)

if __name__ == "__main__":
  sys.exit(main())
