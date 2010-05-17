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

    def load(self):
        self._fnames = ['media/Castlevania - Sonata of the Damned/01 Vampire Snap (Castlevania - Vampire Killer).mp3']

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

    def _lame_enc_stream(self, fname):
        lfile = '/opt/local/bin/lame -b 128 --noreplaygain --quiet "%s" -' % (fname)
        proc = subprocess.Popen(lfile, shell=True, stdout=subprocess.PIPE)
        print "Streaming %s" % (fname)
        return proc

    def run(self):
        self._running = True

        proc = self._lame_enc_stream(self._fnames[0])

        try:
            while(self._running):
                data = proc.stdout.read(2048)
                if not data:
                    os.kill(proc.pid, signal.SIGKILL) # because 2.5 doesn't have terminate()
                    proc = self._lame_enc_stream(self._fnames[0])
                    continue
                    
                try:
                    self._clientlock.acquire()
                    toremove = []
                    for c in self._clients:
                        try:
                            c.wfile.write(data)
                        except socket.error, e:
                            print e
                            toremove.append(c)

                    for tr in toremove:
                        self._clients.remove(tr)

                finally:
                    self._clientlock.release()

                time.sleep(0.125)
        finally:
            proc.terminate()
            
