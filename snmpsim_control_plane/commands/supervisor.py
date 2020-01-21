#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator Control Plane: Process supervisor
#
import argparse
import os
import sys

import snmpsim_control_plane
from snmpsim_control_plane import daemon
from snmpsim_control_plane import log
from snmpsim_control_plane import error
from snmpsim_control_plane.supervisor import manager
from snmpsim_control_plane.supervisor.reporting.manager import ReportingManager


DESCRIPTION = """\
SNMP Simulation Control Plane process supervisor.

Process supervisor watches a directory with potentially changing
executables (e.g. scripts), invokes each and maintains them in running
state for as long as its executable file is in place. On executable
change, the supervisor will restart corresponding processes.

The process supervisor tool is designed to run together with SNMP
simulator configuration management tool.
"""


def parse_args():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument(
        '-v', '--version', action='version',
        version=snmpsim_control_plane.__version__)

    parser.add_argument(
        '--logging-method', type=lambda x: x.split(':'),
        metavar='=<%s[:args]>]' % '|'.join(log.METHODS_MAP),
        default='stderr', help='Logging method')

    parser.add_argument(
        '--log-level', choices=log.LEVELS_MAP,
        type=str, default='info', help='Logging level')

    parser.add_argument(
        '--daemonize', action='store_true',
        help='Disengage from controlling terminal and become a daemon')

    parser.add_argument(
        '--pid-file', metavar='<FILE>', type=str,
        default='/var/run/%s/%s.pid' % (__name__, os.getpid()),
        help='PID file to track supervisor process execution')

    parser.add_argument(
        '--watch-dir', metavar='<DIR>', type=str, required=True,
        help='Location of the executables to herd.')


    parser.add_argument(
        '--reporting-method', type=lambda x: x.split(':'),
        metavar='=<%s[:args]>]' % '|'.join(ReportingManager.REPORTERS),
        default='null', help='SNMP Simulator instance metrics '
                             'reporting method.')

    return parser.parse_args()


def main():
    args = parse_args()

    try:
        log.set_logger(__name__, *args.logging_method, force=True)

        if args.log_level:
            log.set_level(args.log_level)

    except error.ControlPlaneError as exc:
        sys.stderr.write('%s\r\n' % exc)
        return 1

    try:
        ReportingManager.configure(*args.reporting_method)

    except error.ControlPlaneError as exc:
        sys.stderr.write('%s\r\n' % exc)
        return 1

    if args.daemonize:
        try:
            daemon.daemonize(args.pid_file)

        except Exception as exc:
            sys.stderr.write(
                'ERROR: cant daemonize process: %s\r\n' % exc)
            return 1

    manager.manage_executables(args.watch_dir)

    return 0


if __name__ == '__main__':
    sys.exit(main())
