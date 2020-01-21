#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator Control Plane: metrics importer manager
#
from snmpsim_control_plane.metrics.importers import fulljson
from snmpsim_control_plane import log


KNOWN_IMPORTERS = {
    'fulljson': fulljson.import_metrics,
}


def import_metrics(jsondoc):
    """Update metrics DB from `dict` data structure

    The input data structure is expected to be the one produced by SNMP
    simulator's command responder `fulljson` reporting module.
    """
    flavor = jsondoc.get('format')
    importer = KNOWN_IMPORTERS.get(flavor)
    if not importer:
        log.error('Unknown metric flavor %s, '
                  'ignoring' % flavor or '<unspecified>')
        return

    importer(jsondoc)
