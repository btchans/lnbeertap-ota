"""
Websockets client for micropython

Based very heavily off
https://github.com/aaugustin/websockets/blob/master/websockets/client.py

rewritten connect 
    ai = socket.getaddrinfo(uri.hostname, uri.port, socket.SOCK_STREAM)[0]
    s = socket.socket(ai[0], ai[1], ai[2])
    s.connect(ai[-1])

    if uri.protocol == 'wss':
        sock = ussl.wrap_socket(s, server_hostname=uri.hostname)

"""
import usocket as socket
import ubinascii as binascii
import urandom as random
import ussl

from uwebsockets_protocol import Websocket, urlparse


class WebsocketClient(Websocket):
    is_client = True

def connect(uri):
    """
    Connect a websocket.
    """

    uri = urlparse(uri)
    assert uri

    print("open connection %s:%s" % (uri.hostname, uri.port))

    ai = socket.getaddrinfo(uri.hostname, uri.port, socket.SOCK_STREAM)[0]
    s = socket.socket(ai[0], ai[1], ai[2])
    s.connect(ai[-1])

    if uri.protocol == 'wss':
        sock = ussl.wrap_socket(s, server_hostname=uri.hostname)

    def send_header(header, *args):
        #print(header % args + '\r\n')
        sock.write(header % args + '\r\n')

    # Sec-WebSocket-Key is 16 bytes of random base64 encoded
    key = binascii.b2a_base64(bytes(random.getrandbits(8)
                                    for _ in range(16)))[:-1]

    send_header(b'GET %s HTTP/1.1', uri.path or '/')
    send_header(b'Host: %s:%s', uri.hostname, uri.port)
    send_header(b'Connection: Upgrade')
    send_header(b'Upgrade: websocket')
    send_header(b'Sec-WebSocket-Key: %s', key)
    send_header(b'Sec-WebSocket-Version: 13')
    send_header(b'Origin: http://{hostname}:{port}'.format(
        hostname=uri.hostname,
        port=uri.port)
    )
    send_header(b'')

    header = sock.readline()[:-3]
    if header.startswith(b'HTTP/1.1 101 '):
        print("websocket-connection successfully established")
    assert header.startswith(b'HTTP/1.1 101 '), header

    # We don't (currently) need these headers
    # FIXME: should we check the return key?
    while header:
        header = sock.readline()[:-3]

    return WebsocketClient(sock)