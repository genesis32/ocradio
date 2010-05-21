#!/usr/bin/env python

import os

class RecentlyPlayedTracks:
    
    def __init__(self):
        self.recentlist = 'recent.list'
        self.numitems   = 5

    def load(self, config):
        tempdir = config.get('data', 'tempdir')
        if not os.path.isdir(tempdir):
            raise Exception("Temp dir %s not found." % (self._tempdir))

        self.numitems = config.getint('data', 'recentlistsize')
        recentlist = config.get('data', 'recentlist')

        self.recentlist = os.path.join(tempdir, recentlist)

        file(self.recentlist, 'wa').close()

    def update(self, trackname):
        fh = file(self.recentlist, 'r')
        lastfiles = fh.readlines()
        fh.close()

        lastfiles.insert(0, os.path.basename(trackname) + os.linesep)

        fh = file(self.recentlist, 'w')
        fh.writelines(lastfiles[:self.numitems])
        fh.close()

    def get_entries(self):
        fh = file(self.recentlist)
        ret = fh.readlines()
        fh.close()

        return ret
