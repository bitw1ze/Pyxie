import pyxie, sys, re

def mod(data):
  return re.sub(r'Accept-Encoding:.*\r\n', '', data)

def main():
  try:
    pyxie.add_modifier(pyxie.CustomModifier(mod))
    pyxie.start()
  except KeyboardInterrupt as e:
    print e
    pyxie.stop()
    sys.exit(0)

if __name__ == "__main__":
  sys.exit(main())
