#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator: REST API management server
#
import argparse
import os
import sys

from snmpsim_control_plane.management import app
from snmpsim_control_plane.management import db
from snmpsim_control_plane.management import views  # noqa

DESCRIPTION = """\
SNMP Simulation Control Plane REST API server.
 
Maintains SNMP simulator configuration in a DB manageable via REST API.
Generates SNMP simulator invocation script with necessary parameter
realizing the most rest known configuration.

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
             'SNMPSIM_MGMT_CONFIG.')

    parser.add_argument(
        '--interface', type=str,
        help='IP address of the local interface for REST API'
             'server to listen on. Can also be set via config variable '
             'SNMPSIM_MGMT_LISTEN_IP. Default is all local interfaces.')

    parser.add_argument(
        '--port', type=int,
        help='TCP port to bind REST API server to.  Can also be '
             'set via config variable SNMPSIM_MGMT_LISTEN_PORT. '
             'Default is 5000.')

    parser.add_argument(
        '--data-root', type=str,
        help='Path to a SNMP simulation data root directory. SNMP command '
             'responder will be configured with its data files being under '
             'this directory. Can also be set via config variable '
             'SNMPSIM_MGMT_DATAROOT.')

    parser.add_argument(
        '--template', type=str,
        help='Path to Jinja2 template to use for rendering SNMP simulator command '
             'responder invocation command. Can also be set via config variable '
             'SNMPSIM_MGMT_TEMPLATE. By default, built-in template is used.')

    parser.add_argument(
        '--destination', type=str,
        help='Path to a directory where REST API server will place rendered '
             'SNMP simulator command responder invocation scripts. Can also '
             'be set via config variable SNMPSIM_MGMT_DESTINATION.')

    return parser.parse_args()


def main():

    args = parse_args()

    if args.config:
        os.environ['SNMPSIM_MGMT_CONFIG'] = args.config

    config_file = os.environ.get('SNMPSIM_MGMT_CONFIG')
    if config_file:
        app.config.from_pyfile(config_file)

    if args.interface:
        app.config['SNMPSIM_MGMT_LISTEN_IP'] = args.interface

    if args.port:
        app.config['SNMPSIM_MGMT_LISTEN_PORT'] = args.port

    if args.data_root:
        app.config['SNMPSIM_MGMT_DATAROOT'] = args.data_root

    if args.template:
        app.config['SNMPSIM_MGMT_TEMPLATE'] = args.template

    if args.destination:
        app.config['SNMPSIM_MGMT_DESTINATION'] = args.destination

    if args.recreate_db:
        db.drop_all()
        db.create_all()
        return 0

    app.run(host=app.config.get('SNMPSIM_MGMT_LISTEN_IP'),
            port=app.config.get('SNMPSIM_MGMT_LISTEN_PORT'))

    return 0


if __name__ == '__main__':
    sys.exit(main())
