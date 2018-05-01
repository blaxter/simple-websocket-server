'''
The MIT License (MIT)
Copyright (c) 2013 Dave P.
'''

import signal
import ssl
import sys
import threading
import time
from optparse import OptionParser

from SimpleWebSocketServer import (SimpleSSLWebSocketServer, PING, PONG,
                                   SimpleWebSocketServer, WebSocket)


class SimpleEcho(WebSocket):

    def handleMessage(self):
        self.sendMessage(self.data)

    def handleConnected(self):
        self.ping_interval = 5
        self.closing = False

        def ping_worker():
            while not self.closing:
                time.sleep(self.ping_interval)
                print("> PING")
                self._sendMessage(False, PING, "")

        self.ping_thread = threading.Thread(target=ping_worker)
        self.ping_thread.start()

    def handlePong(self):
        print("< PONG")

    def handlePing(self):
        print("Received PING! send PONG!")
        self._sendMessage(False, PONG, self.data)

    def handleClose(self):
        self.closing = True
        self.ping_thread.join()
        print("+EOF")


clients = []


class SimpleChat(WebSocket):

    def handleMessage(self):
        for client in clients:
            if client != self:
                client.sendMessage(self.address[0] + u' - ' + self.data)

    def handleConnected(self):
        print (self.address, 'connected')
        for client in clients:
            client.sendMessage(self.address[0] + u' - connected')
        clients.append(self)

    def handleClose(self):
        clients.remove(self)
        print (self.address, 'closed')
        for client in clients:
            client.sendMessage(self.address[0] + u' - disconnected')


if __name__ == "__main__":

    parser = OptionParser(usage="usage: %prog [options]", version="%prog 1.0")
    parser.add_option("--host", default='', type='string', action="store", dest="host", help="hostname (localhost)")
    parser.add_option("--port", default=8000, type='int', action="store", dest="port", help="port (8000)")
    parser.add_option("--example", default='echo', type='string', action="store", dest="example", help="echo, chat")
    parser.add_option("--ssl", default=0, type='int', action="store", dest="ssl", help="ssl (1: on, 0: off (default))")
    parser.add_option("--cert", default='./cert.pem', type='string',
                      action="store", dest="cert", help="cert (./cert.pem)")
    parser.add_option("--key", default='./key.pem', type='string', action="store", dest="key", help="key (./key.pem)")
    parser.add_option("--ver", default=ssl.PROTOCOL_TLSv1, type=int, action="store", dest="ver", help="ssl version")

    (options, args) = parser.parse_args()

    cls = SimpleEcho
    if options.example == 'chat':
        cls = SimpleChat

    if options.ssl == 1:
        server = SimpleSSLWebSocketServer(options.host, options.port, cls,
                                          options.cert, options.key, version=options.ver)
    else:
        server = SimpleWebSocketServer(options.host, options.port, cls)

    def close_sig_handler(signal, frame):
        server.close()
        sys.exit()

    signal.signal(signal.SIGINT, close_sig_handler)

    server.serveforever()
