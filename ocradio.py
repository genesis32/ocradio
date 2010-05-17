#!/usr/bin/env python

"""
ICY 200 OK
icy-notice1:<BR>This stream requires <a href="http://www.winamp.com/">Winamp</a><BR>
icy-notice2:SHOUTcast Distributed Network Audio Server/win32 v1.9.7<BR>
icy-name:Monkey Radio: Grooving. Sexy. Beats.
icy-genre:funkjazztechnoporn
icy-url:http://monkeyradio.org/
content-type:audio/mpeg
icy-pub:0
icy-br:192
"""

import SocketServer
import time
from   mp3chunker import MP3Chunker

g_mp3chunker = None

class MP3ServeHandler(SocketServer.StreamRequestHandler):
    
    def _send_header(self, str):
        self.wfile.write(str + '\r\n')

    def _send_endheaders(self):
        self.wfile.write('\r\n')

    def handle(self):
        print self.rfile.readline().strip()
        self._send_header('ICY 200 OK')
        self._send_header('icy-name:OCRadio. Video Game ReMiX.')
        self._send_header('icy-genre:Video game music.')
        self._send_header('icy-url:http://www.msynet.com/ocradio/')
        self._send_header('content-type:audio/mpeg')
        self._send_header('icy-pub:0')
        self._send_header('icy-br:128')
        self._send_endheaders();

        global g_mp3chunker
        try:
            g_mp3chunker.add_client(self)
            while(True):
                time.sleep(0.25)
        finally:
            g_mp3chunker.remove_client(self)

def main():
    global g_mp3chunker
    server = None
    try:
        g_mp3chunker = MP3Chunker()
        g_mp3chunker.load()
        g_mp3chunker.start()

        server = SocketServer.ThreadingTCPServer(('', 8989), MP3ServeHandler)
        server.allow_reuse_address = True
        print 'started OCRadio Server...'
        server.serve_forever()
    except:
        if server != None:
            server.socket.close()
        g_mp3chunker.stop()
            
if __name__ == '__main__':
    main()
