# Copyright (C) 1994-2010 by David Massey (davidm@msynet.com)
# See LICENSE for licensing information
"""
Utility functions that don't belong anywhere else.
"""

import os
import daemon
from   daemon import pidlockfile

def daemonize(chdir):
    context = daemon.DaemonContext()

    dirs = { 'run': 'run/', 'logs': 'logs/' }
    for k,v in dirs.items():
        dirs[k] = os.path.join(chdir, v)
        if not os.path.exists(dirs[k]):
            os.mkdir(dirs[k])

    context.pidfile = pidlockfile.PIDLockFile(os.path.join(dirs['run'], "ocradio.pid"))
    context.stdout  = open(os.path.join(dirs['logs'], "ocradio.out"), "a+")
    context.stderr  = open(os.path.join(dirs['logs'], "ocradio.err"), "a+")
    context.working_directory = os.path.expanduser(chdir)

    context.open()

    return context
