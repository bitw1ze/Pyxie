import subprocess
import logging
from OpenSSL import SSL

log = logging.getLogger("pyxie")

class SSLWrapper:

    @staticmethod
    def wrap(stream):
        stream.outbound = SSLWrapper._wrap_outbound(stream.outbound)
        subject = stream.outbound.get_peer_certificate().get_subject()
        stream.inbound = SSLWrapper._wrap_inbound(stream.inbound, subject)

        return stream.inbound, stream.outbound

    @staticmethod
    def _wrap_outbound(sock):

        # TODO: add support for virtual hosts via SNI extension
        # stream.outbound.set_tlsext_host_name(server_name)
        ctx = SSL.Context(SSL.SSLv3_METHOD)
        ctx.set_cipher_list("ALL")
        ctx.set_verify(SSL.VERIFY_NONE, lambda a,b,c,d,e: True)
        sock = SSL.Connection(ctx, sock)
        sock.set_connect_state()
        sock.do_handshake()

        
        return sock

    @staticmethod
    def _wrap_inbound(sock, subject):

        commonName = subject.commonName
        subject_str = ""
        for pair in subject.get_components():
            subject_str += "/%s=%s" % (pair[0].decode('utf8'), 
                                       pair[1].decode('utf8'))
        subject_str += '/'
        log.debug(subject_str)

        # generate the cert
        subprocess.call(["sh", "./gencert.sh", commonName, subject_str])

        certfile = 'cert/newcerts/%s.pem' % commonName
        ctx = SSL.Context(SSL.SSLv3_METHOD)
        ctx.set_cipher_list("ALL")
        ctx.use_privatekey_file(certfile)
        ctx.use_certificate_file(certfile)
        ctx.use_certificate_chain_file(certfile)
        sock = SSL.Connection(ctx, sock)
        sock.set_accept_state()
        sock.do_handshake()

        return sock
        




'''
# XXX: Use this terrible code to extract the subject out of the cert if we end
# up needing ssl over PyOpenSSL

        # get the cert
        sock = ssl.wrap_socket(sock,
                            do_handshake_on_connect=False,
                            server_side=True,
                            certfile=certfile,
                            ssl_version=ssl.PROTOCOL_SSLv3)
        sock.do_handshake()

        # call getpeercert()

        subject_str = ''
        commonName = ''

        # i am so sorry, please kill me
        for field in subject:
            for subfield in field:
                key = field[0][0]
                val = field[0][1]
                if key == 'commonName':
                    subject_str += ('/CN=' + val)
                    commonName = val

                elif key == 'countryName':
                    subject_str += ('/C=' + val)
                elif key == 'organizationName':
                    subject_str += ('/O=' + val)
        subject_str += '/'
        '''

'''
# server-side part

        sock = ssl.wrap_socket(sock,
                               do_handshake_on_connect=False,
                               server_side=False,
                               cert_reqs=ssl.CERT_REQUIRED,
                               ca_certs='./mozilla_cacert.pem',
                               ssl_version=ssl.PROTOCOL_SSLv3)
        sock.do_handshake()
        '''


'''
#TODO: hack together support for virtual hosts via server_name TLS extension
        server_name = sock.get_servername()

        stream.outbound = ssl.wrap_socket(stream.outbound)
        sock = ssl.wrap_socket(sock, server_side=True, certfile="cert/amazon.crt", keyfile="cert/amazon.key", ssl_version=ssl.PROTOCOL_SSLv23)

        subject = stream.outbound.get_peer_certificate().get_subject().commonName
        cert = ssl.DER_cert_to_PEM_cert(stream.outbound.getpeercert(True)).decode('base64')
'''
