#!/usr/bin/env python

import time
import threading
import socket
import subprocess
import os
import signal

class MP3Chunker(threading.Thread):

    def __init__(self):
        threading.Thread.__init__ (self)
        self._fnames   = None
        self._clients  = set()
        self._clientlock = threading.Lock()
        self._lame_exe   = '/usr/local/bin/lame'
        self._trackidx   = 0
        self.bitrate     = 128


    def load(self, config):
        self._lame_exe = config.get('lame', 'exe')
        self.bitrate   = config.getint('lame', 'bitrate')
        self._fnames   = ['media/Castlevania - Sonata of the Damned/01 Vampire Snap (Castlevania - Vampire Killer).mp3']

    def add_client(self, client):
        try:
            self._clientlock.acquire()
            self._clients.add(client)
        finally:
            self._clientlock.release()

    def remove_client(self, client):
        try:
            self._clientlock.acquire()
            self._clients.remove(client)
        finally:
            self._clientlock.release()

    def stop(self):
        self._running = False

    def _next_trackname(self):
        if self._trackidx >= len(self._fnames): 
            self._trackidx = 0

        ret = self._fnames[self._trackidx]
        self._trackidx += 1
        return ret

    def _lame_enc_stream(self, fname):
        lfile = '%s -b %d --noreplaygain --quiet "%s" -' % (self._lame_exe, self.bitrate, fname)
        proc = subprocess.Popen(lfile, shell=True, stdout=subprocess.PIPE)
        print "Streaming %s" % (fname)
        return proc

    def run(self):
        self._running = True

        proc = self._lame_enc_stream(self._next_trackname())
        try:
            while(self._running):
                data = proc.stdout.read(2048)
                if not data:
                    os.kill(proc.pid, signal.SIGKILL) # because 2.5 doesn't have terminate()
                    proc = self._lame_enc_stream(self._next_trackname())
                    continue
                    
                try:
                    self._clientlock.acquire()
                    toremove = []
                    for c in self._clients:
                        try:
                            bytes_to_send = len(data)
                            bytes_sent = 0
                            while bytes_sent < bytes_to_send:
                                bytes_sent += c.send(data)

                        except socket.error, e:
                            print e
                            toremove.append(c)

                    for tr in toremove:
                        tr.close()
                        self._clients.remove(tr)

                finally:
                    self._clientlock.release()

                timetosleep = 2048.0 / ((self.bitrate / 8) * 1024.0)
                time.sleep(timetosleep)
        finally:
            os.kill(proc.pid, signal.SIGKILL) # because 2.5 doesn't have terminate()

            
