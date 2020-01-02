#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator: REST API metrics server
#
import argparse
import os
import sys

from snmpsim_control_plane.metrics import app
from snmpsim_control_plane.metrics import db
from snmpsim_control_plane.metrics import views  # noqa

DESCRIPTION = """\
SNMP Simulation Control Plane metrics REST API server.

Provides user access to metrics database. The user can request
slices of data by specifying data filtering conditions.

Can be run as a WSGI application.
"""


def parse_args():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument(
        '--recreate-db',
        action='store_true',
        help='DANGER! Running with this flag wipes up REST API server DB! '
             'This switch makes sense only when running this tool for the '
             'first time.')

    parser.add_argument(
        '--config', type=str,
        help='Config file path. Can also be set via environment variable '
             'SNMPSIM_METRICS_CONFIG.')

    parser.add_argument(
        '--interface', type=str,
        help='IP address of the local interface for REST API'
             'server to listen on. Can also be set via config variable '
             'SNMPSIM_METRICS_LISTEN_IP. Default is all local interfaces.')

    parser.add_argument(
        '--port', type=int,
        help='TCP port to bind REST API server to.  Can also be '
             'set via config variable SNMPSIM_METRICS_LISTEN_PORT. '
             'Default is 5001.')

    return parser.parse_args()


def main():
    args = parse_args()

    if args.config:
        os.environ['SNMPSIM_METRICS_CONFIG'] = args.config

    config_file = os.environ.get('SNMPSIM_METRICS_CONFIG')
    if config_file:
        app.config.from_pyfile(config_file)

    if args.interface:
        app.config['SNMPSIM_METRICS_LISTEN_IP'] = args.interface

    if args.port:
        app.config['SNMPSIM_METRICS_LISTEN_PORT'] = args.port

    if args.recreate_db:
        db.drop_all()
        db.create_all()
        return 0

    app.run(host=app.config.get('SNMPSIM_METRICS_LISTEN_IP'),
            port=app.config.get('SNMPSIM_METRICS_LISTEN_PORT'))

    return 0


if __name__ == '__main__':
    sys.exit(main())
