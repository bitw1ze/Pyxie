import subprocess
import logging
import socket

from OpenSSL import SSL

from wrappers.base import BaseWrapper


log = logging.getLogger("pyxie")


class SSLWrapper(BaseWrapper):


    @staticmethod
    def wrap(stream):
        stream.server = SSLWrapper._wrap_server(stream.server)
        subject = stream.server.get_peer_certificate().get_subject()
        stream.client = SSLWrapper._wrap_client(stream.client, subject)

        return stream.client, stream.server

    @staticmethod
    def unwrap(stream):

        stream.server.shutdown()
        stream.server.sock_shutdown(socket.RDWR)
        stream.cient.shutdown()
        stream.client.sock_shutdown(socket.RDWR)

    @staticmethod
    def _wrap_server(sock):

        try:
            # TODO: add support for virtual hosts via SNI extension
            # stream.server.set_tlsext_host_name(server_name)
            ctx = SSL.Context(SSL.SSLv23_METHOD)
            ctx.set_cipher_list("ALL")
            ctx.set_verify(SSL.VERIFY_NONE, lambda a,b,c,d,e: True)
            sock = SSL.Connection(ctx, sock)
            sock.set_connect_state()
            sock.do_handshake()
        
        except SSL.SysCallError as e:
            pass
        except SSL.ZeroReturnError as e:
            pass

        return sock

    @staticmethod
    def _wrap_client(sock, subject):

        try:
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

        except SSL.SysCallError as e:
            pass
        except SSL.ZeroReturnError as e:
            pass
