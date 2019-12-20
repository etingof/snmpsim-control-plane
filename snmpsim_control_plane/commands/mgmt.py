#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2010-2019, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator: REST API management server
#
from snmpsim_control_plane.api import app


if __name__ == '__main__':
    app.run()
