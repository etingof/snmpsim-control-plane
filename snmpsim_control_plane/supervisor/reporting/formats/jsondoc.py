#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator Control Plane: Report supervisor metrics in JSON form
#
import json
import os
import socket
import tempfile
import uuid

from snmpsim_control_plane import error
from snmpsim_control_plane import log
from snmpsim_control_plane.supervisor import lifecycle
from snmpsim_control_plane.supervisor.reporting.formats import base


class JsonDocReporter(base.BaseReporter):
    """Dump metrics as a JSON document,

    Metrics are arranged as a data structure like this:

    .. code-block:: python

    {
        'format': 'jsondoc',
        'version': 1,
        'host': '{hostname}',
        'producer': <UUID>,
        'watch_dir': '{dir}',
        'uptime': 0,
        'first_update': '{timestamp}',
        'last_update': '{timestamp}',
        'executables': [
            {
                'executable': '{path}',
                'runtime': '{seconds}',
                'memory': 0,
                'cpu': 0,
                'files': 0,
                'exits': 0,
                'changes': 0,
                'endpoints': {
                    'udpv4': [
                        '127.0.0.1:161'
                    ],
                    'udpv6': [
                        '::1:161'
                    ]
                ],
                'console': [
                    {
                        'timestamp': 0,
                        'text': '{text}'
                    }
                ]
            }
        ]
    }

    """
    REPORTING_FORMAT = 'jsondoc'
    REPORTING_VERSION = 1
    PRODUCER_HOST = socket.gethostname()
    PRODUCER_UUID = str(uuid.uuid1())

    def __init__(self, *args, **kwargs):
        super(JsonDocReporter, self).__init__(*args, **kwargs)

        if not args:
            raise error.ControlPlaneError(
                'Missing %s parameter(s). Expected: '
                '<method>:<reports-dir>[:dumping-period]' % self.__class__.__name__)

        self._reports_dir = os.path.join(args[0], self.REPORTING_FORMAT)

        if len(args) > 1:
            try:
                self.REPORTING_PERIOD = int(args[1])

            except Exception as exc:
                raise error.ControlPlaneError(
                    'Malformed reports dumping period: %s' % args[1])

        try:
            if not os.path.exists(self._reports_dir):
                os.makedirs(self._reports_dir)

        except OSError as exc:
            raise error.ControlPlaneError(
                'Failed to create reports directory %s: '
                '%s' % (self._reports_dir, exc))

        log.debug(
            'Initialized %s metrics reporter for instance %s, metrics '
            'directory %s' % (
                self.__class__.__name__, self.PRODUCER_UUID, self._reports_dir))

    @staticmethod
    def _json_serializer(obj):
        if isinstance(obj, lifecycle.ConsoleLog):
            return [
                {'page': page,
                 'text': obj.text(page),
                 'timestamp': obj.timestamp(page)}
                for page in range(obj.first_page, obj.last_page + 1)
            ]

        return obj

    def dump_metrics(self, metrics, watch_dir=None,
                     started=None, begin=None, end=None):
        """Dump metrics into a JSON file.
        """
        json_metrics = self._format_metrics(metrics)

        json_metrics['format'] = self.REPORTING_FORMAT
        json_metrics['version'] = self.REPORTING_VERSION
        json_metrics['host'] = self.PRODUCER_HOST
        json_metrics['producer'] = self.PRODUCER_UUID
        json_metrics['watch_dir'] = watch_dir
        json_metrics['started'] = started
        json_metrics['first_update'] = int(begin)
        json_metrics['last_update'] = int(end)

        dump_path = os.path.join(self._reports_dir, '%s.json' % end)

        log.debug('Dumping JSON metrics to %s' % dump_path)

        try:
            json_doc = json.dumps(
                json_metrics, indent=2, default=self._json_serializer)

            with tempfile.NamedTemporaryFile(delete=False) as fl:
                fl.write(json_doc.encode('utf-8'))

            os.rename(fl.name, dump_path)

        except Exception as exc:
            log.error(
                'Failure while dumping metrics into '
                '%s: %s' % (dump_path, exc))

    @staticmethod
    def _format_metrics(metrics):
        """Reformat generic metrics into a specific layout
        """
        return {'executables': metrics}
