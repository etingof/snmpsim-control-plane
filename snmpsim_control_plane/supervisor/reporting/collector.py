#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator Control Plane: Process supervisor metrics
#
import collections

import psutil

from snmpsim_control_plane.supervisor import lifecycle
from snmpsim_control_plane import log


ENDPOINT_MAP = {
    'udp4': 'udpv4',
    'udp6': 'udpv6',
    'tcp4': 'tcpv4',
    'tcp6': 'tcpv6',
}

LIFECYCLE_METRICS = (
    'executable',
    'runtime',
    'exits',
    'changes',
    'console'
)


def collect_metrics(*instances):
    """Collect process metrics

    Example
    -------

    .. code-block::

        {
            'executable': '/path/to/executable',
            'memory': 0,  # memory being used (MB, gauge)
            'cpu': 0,  # consumed cpu time (ms, cumulative)
            'files': 0,  # number of open files (gauge)
            'runtime': 0,  # total time this executable has been running (cumulative)
            'exits': 0,  # number of unexpected exits (cumulative)
            'restarts': 0,  # number of restarts because of changes (cumulative)
            'endpoints': {  # allocated network endpoints (gauge)
                'udpv4': [
                    '127.0.0.1:161',
                    '127.0.0.2:161
                ]
            },
            'console': [
                {
                    'timestamp': {time},
                    'text': '{text}
                }
            ]
        }
    """
    all_metrics = []

    for instance in instances:
        pid = instance['pid']
        if not pid:
            continue

        try:
            process = psutil.Process(pid)

            process_info = process.as_dict()

            endpoints = collections.defaultdict(list)

            for kind in ENDPOINT_MAP:
                for conn in process.connections(kind):
                    endpoints[ENDPOINT_MAP[kind]].append(
                        '%s:%s' % (conn.laddr.ip, conn.laddr.port)
                    )

        except psutil.Error as exc:
            log.error(exc)
            continue

        endpoints = collections.defaultdict(list)

        for kind in ENDPOINT_MAP:
            for conn in process.connections(kind):
                endpoints[ENDPOINT_MAP[kind]].append(
                    '%s:%s' % (conn.laddr.ip, conn.laddr.port)
                )

        metrics = {
            'memory': lifecycle.Gauge(
                process_info['memory_info'].vms // 1024 // 1024),
            'cpu': lifecycle.Counter(
                (process_info['cpu_times'].user +
                 process_info['cpu_times'].system) * 1000),
            'endpoints': endpoints,
            'files': lifecycle.Gauge(process_info['num_fds']),
        }

        metrics.update(
            **{metric: instance[metric] for metric in LIFECYCLE_METRICS})

        all_metrics.append(metrics)

    return all_metrics
