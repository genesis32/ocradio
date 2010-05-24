#!/usr/bin/env python

import ConfigParser
import socket
import select
import time
from   mp3chunker import MP3Chunker
from   dataloggers import InstantaneousDataLog

g_mp3chunker = None

class ServerListener:

    def __init__(self):
        self.port = 8989
        self._maxusers = 5
        self._curruserfile = '/tmp/curruser.stats'

    def _write_header(self, client, str):
        client.send(str + '\r\n')

    def _write_endheaders(self, client):
        client.send('\r\n')

    def _send_icy_header(self, client):
        global g_mp3chunker

        self._write_header(client, 'ICY 200 OK')
        self._write_header(client, 'icy-name:OCXRadio. OverClocked ReMix Radio.')
        self._write_header(client, 'icy-genre:Video Game.')
        self._write_header(client, 'icy-url:http://www.msynet.com/ocxradio/')
        self._write_header(client, 'content-type:audio/mpeg')
        self._write_header(client, 'icy-pub:0')
        self._write_header(client, 'icy-metaint:%d' % (MP3Chunker.ChunkSize))
        self._write_header(client, 'icy-br:%d' % (g_mp3chunker.bitrate))
        self._write_endheaders(client);

    def load(self, config):
        self.port = config.getint('network', 'port')
        self._maxusers = config.getint('network', 'maxusers')
        self._curruserfile = config.get('data', 'curruserstats')

    def close(self):
        pass

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
                    data = conn.recv(1024)
                    if not data: continue
                    print data

                    if g_mp3chunker.numusers >= self._maxusers:
                        self._write_header(conn, 'ICY 400 SERVER FULL')
                        self._write_endheaders(conn)
                        conn.close()
                    else:
                        self._send_icy_header(conn)
                        g_mp3chunker.add_client(conn)

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
