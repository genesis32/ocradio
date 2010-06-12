#!/usr/bin/env python

# Copyright (C) 1994-2010 by David Massey (davidm@msynet.com)
# See LICENSE for licensing information

import sys
import os
import socket
import select
import time
import getopt
import re

import ConfigParser

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

    def _get_header(self, sock, max_bytes):
        hdr = ''
        while True:
            rls, wls, xls = select.select([sock], [], [], 0.50)
            if sock not in rls:
                break

            buff = sock.recv(1024)
            if len(buff) == 0 or len(buff) >= max_bytes:
                break

            hdr += buff
            if len(hdr) >= 4 and hdr[-4:] == '\r\n\r\n':
                break

        return hdr


    def serve(self):
        global g_mp3chunker

        print 'Starting OCRadio Server on port %d' % (self.port)

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

                    if g_mp3chunker.numusers >= self._maxusers:
                        self._write_header(conn, 'ICY 400 SERVER FULL')
                        self._write_endheaders(conn)
                        conn.close()
                    else:
                        clienthdr = self._get_header(conn, 8192)

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

def usage():
    exename = os.path.basename(sys.argv[0])
    print >> sys.stderr, "%s - Streaming MP3 Server (http://www.msynet.com/ocxradio)" % (exename)
    print >> sys.stderr
    print >> sys.stderr, "usage: %s [options]" % (exename)
    print >> sys.stderr
    print >> sys.stderr, "OPTIONS" 
    print >> sys.stderr
    print >> sys.stderr, "-h --help                print this help message"
    print >> sys.stderr, "-c --config <cfg file>   config file to read (default: default.cfg)"

def run():
    global g_mp3chunker
    server = None

    configfile = 'default.cfg'
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hc:', ['help', 'config'])

        for opt, arg in opts:
            if opt in ('-h', '--help'):
                usage()
                sys.exit(0)
            if opt in ('-c', '--config'):
                configfile = arg 

    except getopt.GetoptError:
        usage()
        sys.exit(2)

    if not os.path.isfile(configfile):
        print >> sys.stderr, "Config file %s does not exist!" % (configfile)
        usage()
        sys.exit(1)

    config = ConfigParser.ConfigParser()

    try:
        fh = file(configfile)
        config.readfp(fh)
    finally:
        fh.close()
    
    g_mp3chunker = MP3Chunker()
    g_mp3chunker.load(config)
    g_mp3chunker.start()

    server = ServerListener()
    server.load(config)

    server.serve()

    server.close()
    g_mp3chunker.stop()
            
if __name__ == '__main__':
    run()
