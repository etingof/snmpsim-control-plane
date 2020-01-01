#
# This file is part of SNMP Simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
import sys

from snmpsim_control_plane import error

if sys.platform[:3] == 'win':

    def daemonize(pidfile):
        raise error.ControlPlaneError(
            'Windows is not inhabited with daemons!')

else:

    import os
    import atexit
    import signal
    import tempfile


    def daemonize(pidfile):
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                os._exit(0)

        except OSError as exc:
            raise error.ControlPlaneError(
                'ERROR: fork #1 failed: %s' % exc)

        # decouple from parent environment
        try:
            os.chdir('/')
            os.setsid()

        except OSError:
            pass

        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                os._exit(0)

        except OSError as exc:
            raise error.ControlPlaneError(
                'ERROR: fork #2 failed: %s' % exc)

        def signal_cb(s, f):
            raise KeyboardInterrupt

        for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP,
                  signal.SIGQUIT):
            signal.signal(s, signal_cb)

        # write pidfile
        def atexit_cb():
            try:
                if pidfile:
                    os.remove(pidfile)

            except OSError:
                pass

        atexit.register(atexit_cb)

        try:
            if pidfile:
                fd, nm = tempfile.mkstemp(dir=os.path.dirname(pidfile))
                os.write(fd, ('%d\n' % os.getpid()).encode('utf-8'))
                os.close(fd)
                os.rename(nm, pidfile)

        except Exception as exc:
            raise error.ControlPlaneError(
                'Failed to create PID file %s: %s' % (pidfile, exc))

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(os.devnull, 'r')
        so = open(os.devnull, 'a+')
        se = open(os.devnull, 'a+')

        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
