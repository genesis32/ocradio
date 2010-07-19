# Copyright (C) 1994-2010 by David Massey (davidm@msynet.com)
# See LICENSE for licensing information

import os
import sys
import time
import select
import socket
import signal
import subprocess
import threading

import dataloggers
from   dataloggers import InstantaneousDataLog
from   metadata    import MP3Metadata


class MP3Client:

    def __init__(self):
        self.sock = None
        self.supportsmetadata = False
        self.bytestometadata = MP3Chunker.ChunkSize

class MP3Chunker(threading.Thread):
    ChunkSize = 4096

    def __init__(self):
        threading.Thread.__init__ (self)
        self._filelist = None
        self._fnames   = None
        self._clients  = {}
        self._clientlock = threading.Lock()
        self._lame_exe   = '/usr/local/bin/lame'
        self._trackidx   = 0
        self._songidxfile = '/tmp/song.idx'
        self._metadata    = None
        self.bitrate      = 128
        self.numusers     = 0
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

        self._songidxfile = config.get('data', 'songindex')

        fh = file(self._filelist)
        self._fnames = [line.rstrip() for line in fh.readlines()]
        fh.close()

        self.recent_tracks.load(config)

        print "Queued %d songs." % (len(self._fnames))

    def add_client(self, client):
        try:
            self._clientlock.acquire()
            self._clients[client.sock] = client
            self.numusers += 1
        finally:
            self._clientlock.release()

    def stop(self):
        self._running = False

    def _next_trackname(self):
        if self._trackidx >= len(self._fnames): 
            self._trackidx = 0

        nextfilename = self._fnames[self._trackidx]

        InstantaneousDataLog.dumpvalue(self._songidxfile, str(self._trackidx)) 

        self.recent_tracks.update(nextfilename)

        mp3data = MP3Metadata()
        mp3data.load(nextfilename)
        self._metadata = mp3data.get_shoutcast_metadata()

        self._trackidx += 1

        return nextfilename

    def _lame_enc_stream(self, fname):
        lfile = '%s -b %d --noreplaygain --quiet "%s" -' % (self._lame_exe, self.bitrate, fname)
        proc = subprocess.Popen(lfile, shell=True, stdout=subprocess.PIPE)
        print "Streaming %s" % (fname)
        return proc

    def _remove_client(self, client):
        client.sock.close()
        del self._clients[client.sock]
        self.numusers -= 1
        print "Removed client"

    def _send_bytes(self, sock, bytes):
        bytes_to_send = len(bytes)
        bytes_sent = 0
        while bytes_sent < bytes_to_send:
            bytes_sent += sock.send(bytes[bytes_sent:])

    def _send_data(self, client, bytes):
        """ This function assumes that bytes is never more than 2x ChunkSize """
        if not client.supportsmetadata:
            self._send_bytes(client.sock, bytes)
        else:
            if client.bytestometadata < len(bytes):
                self._send_bytes(client.sock, bytes[:client.bytestometadata])
                self._send_bytes(client.sock, self._metadata)
                self._send_bytes(client.sock, bytes[client.bytestometadata:])
                client.bytestometadata = MP3Chunker.ChunkSize - len(bytes[client.bytestometadata:])
            else:
                client.bytestometadata -= len(bytes)
                self._send_bytes(client.sock, bytes)

    def run(self):
        self._running = True

        proc = self._lame_enc_stream(self._next_trackname())
        try:
            # time to sleep inbetweeen chunk sends..
            timetosleep = float(MP3Chunker.ChunkSize) / ((self.bitrate / 8) * 1024.0)
            while(self._running):
                start = time.time()

                data = proc.stdout.read(MP3Chunker.ChunkSize)
                if not data:
                    os.kill(proc.pid, signal.SIGKILL) # because 2.5 doesn't have terminate()
                    proc = self._lame_enc_stream(self._next_trackname())
                    continue

                try:
                    self._clientlock.acquire()

                    csocks = self._clients.keys()
                    
                    r, w, e = select.select(csocks, csocks, [], 0)
                    for sock in w:
                        try:
                            self._send_data(self._clients[sock], data)

                        except socket.error, e:
                            self._remove_client(self._clients[sock])
                            
                    for sock in r:
                        if sock in self._clients:
                            try:
                                bytes = sock.recv(1024)
                                if len(bytes) == 0:
                                    self._remove_client(self._clients[sock])
                            except socket.error, e:
                                self._remove_client(self._clients[sock])
                                
                finally:
                    self._clientlock.release()

                elapsed = time.time() - start

                sleepytime = timetosleep - elapsed
                if sleepytime > 0:
                    time.sleep(sleepytime)

        finally:
            for client in self._clients.values():
                client.sock.close()

            self._clients = {}
            self._numusers = 0
            os.kill(proc.pid, signal.SIGKILL) # because 2.5 doesn't have terminate()

            
