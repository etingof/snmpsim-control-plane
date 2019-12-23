#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator: REST API management server
#
import argparse
import os
import ssl
import sys

from snmpsim_control_plane.api import app
from snmpsim_control_plane.api import db
from snmpsim_control_plane.api.views import mgmt  #noqa

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
        '--interface',
        type=str, default='127.0.0.1',
        help='IP address of the local interface for REST API'
             'server to listen on. Can also be set via config variable '
             'SNMPSIM_MGMT_LISTEN_IP. Default is all local interfaces.')

    parser.add_argument(
        '--port',
        type=int, default=8000,
        help='TCP port to bind REST API server to.  Can also be '
             'set via config variable SNMPSIM_MGMT_LISTEN_PORT. '
             'Default is 8000.')

    parser.add_argument(
        '--ssl-certificate',
        type=str,
        help='SSL certificate to use for HTTPS. Can also be set via '
             'config variable SNMPSIM_MGMT_SSL_CERT.')

    parser.add_argument(
        '--ssl-key',
        type=str,
        help='SSL key to use for HTTPS. Can also be set via config variable '
             'SNMPSIM_MGMT_SSL_KEY.')

    parser.add_argument(
        '--data-root',
        type=str, default='/use/share/snmpsim/data',
        help='Path to a SNMP simulation data root directory. SNMP command '
             'responder will be configured with its data files being under '
             'this directory. Can also be set via config variable '
             'SNMPSIM_MGMT_DATAROOT.')

    parser.add_argument(
        '--template',
        type=str, default='snmpsim-command-responder.j2',
        help='Path to Jinja2 template to use for rendering SNMP simulator command '
             'responder invocation command. Can also be set via config variable '
             'SNMPSIM_MGMT_TEMPLATE. By default, built-in template is used.')

    parser.add_argument(
        '--destination',
        type=str, default='.',
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

    if args.ssl_certificate:
        app.config['SNMPSIM_MGMT_SSL_CERT'] = args.ssl_certificate

    if args.ssl_key:
        app.config['SNMPSIM_MGMT_SSL_KEY'] = args.ssl_key

    ssl_context = None
    ssl_certificate = app.config.get('SNMPSIM_MGMT_SSL_CERT')
    ssl_key = app.config.get('SNMPSIM_MGMT_SSL_KEY')

    if ssl_certificate and ssl_key:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        ssl_context.load_cert_chain(ssl_certificate, ssl_key)

    if args.template:
        app.config['SNMPSIM_MGMT_TEMPLATE'] = args.template

    if args.destination:
        app.config['SNMPSIM_MGMT_DESTINATION'] = args.destination

    if args.recreate_db:
        db.drop_all()
        db.create_all()
        return 0

    app.run(host=app.config.get('SNMPSIM_MGMT_LISTEN_IP'),
            port=app.config.get('SNMPSIM_MGMT_LISTEN_PORT'),
            ssl_context=ssl_context)

    return 0


if __name__ == '__main__':
    sys.exit(main())
