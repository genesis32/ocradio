#!/usr/bin/env python

import ConfigParser
import socket
import select
import time
import re

from   mp3chunker import MP3Chunker, MP3Client
from   dataloggers import InstantaneousDataLog

g_mp3chunker = None

class ServerListener:

    def __init__(self):
        self.port = 8989
        self._maxusers = 5
        self._curruserfile = '/tmp/curruser.stats'

    def _write_header(self, sock, str):
        sock.send(str + '\r\n')

    def _write_endheaders(self, sock):
        sock.send('\r\n')

    def _send_icy_header(self, client):
        global g_mp3chunker

        self._write_header(client.sock, 'ICY 200 OK')
        self._write_header(client.sock, 'icy-name:OCXRadio. OverClocked ReMix Radio.')
        self._write_header(client.sock, 'icy-genre:Video Game.')
        self._write_header(client.sock, 'icy-url:http://www.msynet.com/ocxradio/')
        self._write_header(client.sock, 'content-type:audio/mpeg')
        self._write_header(client.sock, 'icy-pub:0')

        if client.supportsmetadata:
            self._write_header(client.sock, 'icy-metaint:%d' % (MP3Chunker.ChunkSize))

        self._write_header(client.sock, 'icy-br:%d' % (g_mp3chunker.bitrate))
        self._write_endheaders(client.sock);

    def load(self, config):
        self.port = config.getint('network', 'port')
        self._maxusers = config.getint('network', 'maxusers')
        self._curruserfile = config.get('data', 'curruserstats')

    def close(self):
        pass

    def _supports_metadata(self, clienthdr):
        try:
            m = re.search('icy-metadata\:\s*(?P<enabled>\d+)', clienthdr, re.IGNORECASE)
            return m.groups('enabled')[0] == '1'
        except:
            pass
        return False

    def serve(self):
        global g_mp3chunker

        print 'starting OCRadio Server...'

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', self.port))
        s.listen(5)

        running = True
        while running:
            try:
                rls, wls, xls = select.select([s], [], [], 0.50)
                if len(rls) > 0:

                    conn, addr = s.accept()

                    print "Accepted a connection from ", addr
                    clienthdr = ''
                    buff = conn.recv(1024)
                    if buff[-4:] == '\r\n\r\n':
                        clienthdr = buff

                    if g_mp3chunker.numusers >= self._maxusers:
                        self._write_header(conn, 'ICY 400 SERVER FULL')
                        self._write_endheaders(conn)
                        conn.close()
                    else:
                        client = MP3Client()
                        client.sock = conn
                        client.supportsmetadata = self._supports_metadata(clienthdr)

                        self._send_icy_header(client)
                        g_mp3chunker.add_client(client)

                ustr = str(g_mp3chunker.numusers) + "/" + str(self._maxusers)
                InstantaneousDataLog.dumpvalue(self._curruserfile, ustr)

            except KeyboardInterrupt:
                running = False

        s.close()

def main():
    global g_mp3chunker
    server = None

    config = ConfigParser.ConfigParser()
    config.readfp(file('default.cfg'))
    
    g_mp3chunker = MP3Chunker()
    g_mp3chunker.load(config)
    g_mp3chunker.start()

    server = ServerListener()
    server.load(config)

    # loop

    server.serve()

    server.close()
    g_mp3chunker.stop()
            
if __name__ == '__main__':
    main()
