#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator Control Plane: Process supervisor metrics
#


class BaseReporter(object):
    """Maintain activity metrics.
    """
    def __init__(self, *args, **kwargs):
        pass

    def dump_metrics(self, metrics, watch_dir=None,
                     started=None, begin=None, end=None):
        """Dump metrics in a reporter-specific way.
        """

    def __str__(self):
        return self.__class__.__name__
