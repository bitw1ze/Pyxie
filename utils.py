import socket
import re

def getrealdest(csock):   
    """
    SO_ORIGINAL_DST = 80
    odestdata = csock.getsockopt(socket.SOL_IP, SO_ORIGINAL_DST, 16)
    _, port, a1, a2, a3, a4 = struct.unpack("!HHBBBBxxxxxxxx", odestdata)
    address = "%d.%d.%d.%d" % (a1, a2, a3, a4)
    
    return (address, port)
    """
    return ('defcon.org', 443)

def printable_ascii(data):
    return re.sub(r'\s', ' ', 
           re.sub(r'[^ -~]', r'.', data.decode('utf8', 'ignore')))

def dump_ascii(payload, step=16):
    payload = printable_ascii(payload)
    arraydump = []
    for i in range(0, len(payload), step):
        line_end = i + step if i+step < len(payload) else len(payload)
        line = payload[i:line_end]
        arraydump.append(line)
    return arraydump

def dump_hex(payload, step=32):
    payload = b16encode(bytes(payload)).decode('utf8')
    arraydump = []
    for i in range(0, len(payload), step):
        line_end = i + step if i+step < len(payload) else len(payload)
        line = ""
        for j in range(i, line_end, 2):
            line += (payload[j:j+2] + " ")
        arraydump.append(line)

    return arraydump

def dump_asciihex(payload, bytes_per_line=16):
    arraydump = list(zip(dump_hex(payload), dump_ascii(payload)))
    format_str = '%-' + str(bytes_per_line * 3) + 's  %s'
    return "\n".join([format_str % (line[0], line[1]) for line in arraydump])
