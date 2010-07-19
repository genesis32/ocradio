# Copyright (C) 1994-2010 by David Massey (davidm@msynet.com)
# See LICENSE for licensing information

import struct 
from mutagen.easyid3 import EasyID3

class MP3Metadata:

    def __init__(self):
        self.taginfo = None
        pass

    def load(self, fname):
        try:
            self.taginfo = EasyID3(fname)
        except:
            print "No Id3 tag for", fname
            self.taginfo = None

    def get_shoutcast_metadata(self):
        shouttitle = ""
        numbytes   = 0
        try:
            if self.taginfo:
                artist = ''
                if 'artist' in self.taginfo:
                    artist = self.taginfo['artist']
                    
                title = ''
                if 'title' in self.taginfo:
                    title = self.taginfo['title']

                shouttitle = "StreamTitle='" + artist[0] + " - " + title[0] + "';";
            else:
                shouttitle = "StreamTitle='';"
        except:
            shouttitle = "StreamTitle='';"

        bufflen = len(shouttitle)
        numbytes = (bufflen - (bufflen % 16)) + 16

        shouttitle = shouttitle.encode('utf-8')

        metalen  = struct.pack('1B', numbytes/16)
        metadata = struct.pack('%ds' % (numbytes), str(shouttitle))

        return metalen + metadata


