#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator: REST API metrics server
#


class DefaultConfig(object):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory'
    SQLALCHEMY_ECHO = False

    DEBUG = False

    SNMPSIM_METRICS_LISTEN_IP = '127.0.0.1'
    SNMPSIM_METRICS_LISTEN_PORT = 5001
    SNMPSIM_METRICS_SSL_CERT = None
    SNMPSIM_METRICS_SSL_KEY = None
