#!/usr/bin/env python

import os
import sys
import time
import select
import socket
import signal
import subprocess
import threading

import dataloggers

class MP3Chunker(threading.Thread):
    ChunkSize = 2048

    def __init__(self):
        threading.Thread.__init__ (self)
        self._filelist = None
        self._fnames   = None
        self._clients  = set()
        self._clientlock = threading.Lock()
        self._lame_exe   = '/usr/local/bin/lame'
        self._trackidx   = 0
        self._tempdir    = '/tmp/'
        self.bitrate     = 128
        self.numusers    = 0
        self.recent_tracks = dataloggers.RecentlyPlayedTracks()

    def load(self, config):

        self._trackidx = config.getint('data', 'starttrack')

        self._lame_exe = config.get('lame', 'exe')
        if not os.path.isfile(self._lame_exe):
            raise Exception("The lame executable does not exist at %s." % (self._lame_exe))
            
        self.bitrate   = config.getint('lame', 'bitrate')
        if self.bitrate < 0 or self.bitrate > 1024:
            raise Exception("Set your bitrate to between 0 and 1024 not %d." % (self.bitrate))

        self._filelist = config.get('data', 'songlist')
        if not os.path.isfile(self._filelist):
            raise Exception("Songlist file %s not found." % (self._filelist))

        self._tempdir = config.get('data', 'tempdir')
        if not os.path.isdir(self._tempdir):
            raise Exception("Temp dir %s not found." % (self._tempdir))

        fh = file(self._filelist)
        self._fnames = [line.rstrip() for line in fh.readlines()]
        fh.close()

        self.recent_tracks.load(config)

        print "Queued %d songs." % (len(self._fnames))

    def add_client(self, client):
        try:
            self._clientlock.acquire()
            self._clients.add(client)
            self.numusers += 1
        finally:
            self._clientlock.release()

    def stop(self):
        self._running = False

    def _next_trackname(self):
        if self._trackidx >= len(self._fnames): 
            self._trackidx = 0

        ret = self._fnames[self._trackidx]

        # replace this with another 
        fs = os.path.join(self._tempdir, 'song.idx')
        fh = file(fs, 'w')
        fh.write(str(self._trackidx))
        fh.close()

        self.recent_tracks.update(ret)

        self._trackidx += 1

        return ret

    def _lame_enc_stream(self, fname):
        lfile = '%s -b %d --noreplaygain --quiet "%s" -' % (self._lame_exe, self.bitrate, fname)
        proc = subprocess.Popen(lfile, shell=True, stdout=subprocess.PIPE)
        print "Streaming %s" % (fname)
        return proc

    def _remove_client(self, client):
        client.close()
        self._clients.remove(client)
        self.numusers -= 1
        print "Removed client"

    def run(self):
        self._running = True

        proc = self._lame_enc_stream(self._next_trackname())
        try:
            # time to sleep inbetweeen chunk sends..
            timetosleep = float(MP3Chunker.ChunkSize) / ((self.bitrate / 8) * 1024.0)
            while(self._running):
                data = proc.stdout.read(MP3Chunker.ChunkSize)
                if not data:
                    os.kill(proc.pid, signal.SIGKILL) # because 2.5 doesn't have terminate()
                    proc = self._lame_enc_stream(self._next_trackname())
                    continue
                
                start = time.time()
                try:
                    self._clientlock.acquire()
                    
                    r, w, e = select.select(self._clients, self._clients, [], 0)
                    for client in w:
                        try:
                            bytes_to_send = len(data)
                            bytes_sent = 0
                            while bytes_sent < bytes_to_send:
                                bytes_sent += client.send(data[bytes_sent:])
                        except socket.error, e:
                            self._remove_client(client)
                            
                    for client in r:
                        if client in self._clients:
                            bytes = client.recv(1024)
                            if len(bytes) == 0:
                                self._remove_client(client)
                                
                finally:
                    self._clientlock.release()

                elapsed = time.time() - start
                time.sleep(timetosleep - elapsed)
        finally:
            for tr in self._clients:
                tr.close()
            self._clients = []
            self._numusers = 0
            os.kill(proc.pid, signal.SIGKILL) # because 2.5 doesn't have terminate()

            
