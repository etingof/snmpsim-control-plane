#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator Control Plane: supervisor metrics reporting manager
#
import collections
import time

from snmpsim_control_plane import error
from snmpsim_control_plane import log
from snmpsim_control_plane.supervisor import lifecycle
from snmpsim_control_plane.supervisor.reporting import collector
from snmpsim_control_plane.supervisor.reporting.formats import jsondoc
from snmpsim_control_plane.supervisor.reporting.formats import null


class ReportingManager(object):
    """Gather and dump activity metrics.

    For each of given managed process instances, collect OS-level
    metrics.

    Then write them down as a JSON file indexed by time. Consumers
    are expected to process each of these files and are free to remove
    them.
    """

    REPORTING_PERIOD = 15

    REPORTERS = {
        'null': null.NullReporter,
        'jsondoc': jsondoc.JsonDocReporter,
    }

    STARTED = int(time.time())

    _last_reportings = collections.defaultdict(dict)

    _reporter = null.NullReporter()

    _next_dump = time.time() + REPORTING_PERIOD

    @classmethod
    def configure(cls, fmt, *args):
        try:
            reporter = cls.REPORTERS[fmt]

        except KeyError:
            raise error.ControlPlaneError(
                'Unsupported reporting format: %s' % fmt)

        cls._reporter = reporter(*args)

        log.info('Using "%s" activity reporting method with '
                 'params %s' % (cls._reporter, ', '.join(args)))

    @classmethod
    def process_metrics(cls, watch_dir, *instances):
        now = int(time.time())

        if cls._next_dump > now:
            return

        last_dump = cls._next_dump - cls.REPORTING_PERIOD
        cls._next_dump = now + cls.REPORTING_PERIOD

        all_metrics = collector.collect_metrics(*instances)

        for metrics in all_metrics:
            executable = metrics['executable']

            last_reportings = cls._last_reportings[executable]

            for metric, value in metrics.items():
                if not isinstance(value, lifecycle.AbstractGrowingValue):
                    continue

                # compute the difference in value growth to report

                previous_value = last_reportings.get(metric)
                current_value = metrics.get(metric)

                last_reportings[metric] = current_value.latest

                metrics[metric] = current_value.added_content(previous_value)

        cls._reporter.dump_metrics(
            all_metrics, watch_dir=watch_dir, started=cls.STARTED,
            begin=int(last_dump), end=int(now))
