#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator: REST API management server
#


class DefaultConfig(object):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory'
    SQLALCHEMY_ECHO = False

    DEBUG = False

    SNMPSIM_MGMT_LISTEN_IP = '127.0.0.1'
    SNMPSIM_MGMT_LISTEN_PORT = 5000
    SNMPSIM_MGMT_SSL_CERT = None
    SNMPSIM_MGMT_SSL_KEY = None
    SNMPSIM_MGMT_DATAROOT = '/usr/share/snmpsim/data'
    SNMPSIM_MGMT_TEMPLATE = 'snmpsim-command-responder.j2'
    SNMPSIM_MGMT_DESTINATION = '.'
