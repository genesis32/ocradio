# Copyright (C) 1994-2010 by David Massey (davidm@msynet.com)
# See LICENSE for licensing information

import os

class InstantaneousDataLog:
    def dumpvalue(fname, str):
        try:
            fh = file(fname, 'w')
            fh.write(str)
        finally:
            fh.close()
    dumpvalue = staticmethod(dumpvalue)

class RecentlyPlayedTracks:
    
    def __init__(self):
        self.numitems   = 5
        self.recentlistfile = '/tmp/recent.list'

    def load(self, config):
        self.numitems = config.getint('data', 'recentlistsize')
        self.recentlistfile = config.get('data', 'recentlist')

        file(self.recentlistfile, 'wa').close()

    def update(self, trackname):
        fh = file(self.recentlistfile, 'r')
        lastfiles = fh.readlines()
        fh.close()

        lastfiles.insert(0, os.path.basename(trackname) + os.linesep)

        fh = file(self.recentlistfile, 'w')
        fh.writelines(lastfiles[:self.numitems])
        fh.close()

    def get_entries(self):
        fh = file(self.recentlistfile)
        ret = fh.readlines()
        fh.close()

        return ret
