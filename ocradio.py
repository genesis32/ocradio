#!/usr/bin/env python

import ConfigParser
import socket
import time
from   mp3chunker import MP3Chunker

g_mp3chunker = None

class ServerListener:

    def __init__(self):
        pass

    def _write_header(self, client, str):
        client.send(str + '\r\n')

    def _write_endheaders(self, client):
        client.send('\r\n')

    def _send_icy_header(self, client):
        global g_mp3chunker

        self._write_header(client, 'ICY 200 OK')
        self._write_header(client, 'icy-name:OCRadio. Video Game ReMiX.')
        self._write_header(client, 'icy-genre:Video game music.')
        self._write_header(client, 'icy-url:http://www.msynet.com/ocradio/')
        self._write_header(client, 'content-type:audio/mpeg')
        self._write_header(client, 'icy-pub:0')
        self._write_header(client, 'icy-br:%d' % (g_mp3chunker.bitrate))
        self._write_endheaders(client);

    def close(self):
        pass

    def serve(self):
        global g_mp3chunker

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', 8989))
        s.listen(1)

        while True:
            conn, addr = s.accept()
            print "Accepted connection"
            data = conn.recv(1024)
            if not data: continue

            print data
            self._send_icy_header(conn)
            
            g_mp3chunker.add_client(conn)

def main():
    global g_mp3chunker
    server = None
    try:
        config = ConfigParser.ConfigParser()
        config.readfp(file('default.cfg'))

        g_mp3chunker = MP3Chunker()
        g_mp3chunker.load(config)
        g_mp3chunker.start()

        server = ServerListener()
        print 'started OCRadio Server...'
        server.serve()
    except Exception, e:
        print e
        if server != None:
            server.close()
        g_mp3chunker.stop()
            
if __name__ == '__main__':
    main()
