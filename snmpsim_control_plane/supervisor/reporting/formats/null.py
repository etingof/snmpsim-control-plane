#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator Control Plane: Do not report supervisor metrics
#
from snmpsim_control_plane.supervisor.reporting.formats import base


class NullReporter(base.BaseReporter):
    """No-op activity metrics reporter.
    """
