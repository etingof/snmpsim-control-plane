#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator: metrics importing tool
#
import argparse
import sys
import os

import snmpsim_control_plane
from snmpsim_control_plane import daemon
from snmpsim_control_plane import error
from snmpsim_control_plane import log
from snmpsim_control_plane.metrics import app
from snmpsim_control_plane.metrics import db
from snmpsim_control_plane.metrics import reader
from snmpsim_control_plane.metrics import models  # noqa

DESCRIPTION = """\
SNMP Simulation Control Plane metrics importer.

Watches given directory for metrics JSON files to appear,
load them into ORM and remove once processed.
"""


class DefaultConfig(object):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory'
    SQLALCHEMY_ECHO = False

    DEBUG = False


def parse_args():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument(
        '-v', '--version', action='version',
        version=snmpsim_control_plane.__version__)

    parser.add_argument(
        '--recreate-db',
        action='store_true',
        help='DANGER! Running with this flag wipes up metrics DB! '
             'This switch makes sense only when running this tool for the '
             'first time.')

    parser.add_argument(
        '--config', type=str,
        help='Config file path. Can also be set via environment variable '
             'SNMPSIM_METRICS_CONFIG.')

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
        help='PID file to track daemon process execution')

    parser.add_argument(
        '--watch-dir', metavar='<DIR>', type=str,
        help='Location of the metrics JSON files to import and remove.')

    return parser.parse_args()


def main():
    args = parse_args()

    app.config.from_object(DefaultConfig)

    if args.config:
        app.config.from_pyfile(args.config)

    if args.recreate_db:
        db.drop_all()
        db.create_all()
        return 0

    if not args.watch_dir:
        sys.stderr.write('ERROR: --watch-dir must be specified\r\n')
        return 1

    try:
        log.set_logger(__name__, *args.logging_method, force=True)

        if args.log_level:
            log.set_level(args.log_level)

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

    reader.watch_metrics(args.watch_dir)

    return 0


if __name__ == '__main__':
    sys.exit(main())
