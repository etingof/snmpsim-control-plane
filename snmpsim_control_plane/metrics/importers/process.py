#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator metrics: supervisor metrics importer
#
import datetime
import time

from snmpsim_control_plane.metrics import db
from snmpsim_control_plane.metrics import models
from snmpsim_control_plane.metrics.utils import autoincrement

MAX_CONSOLE_PAGE_AGE = 86400  # one day


def import_metrics(jsondoc):
    """Update metrics DB from `dict` data structure

    The input data structure is expected to be the one produced by SNMP
    simulator's command responder `fulljson` reporting module.



    .. code-block:: python

    {
        'format': 'jsondoc',
        'version': 1,
        'host': '{hostname}',
        'watch_dir': {dir},
        'started': '{timestamp}',
        'first_update': '{timestamp}',
        'last_update': '{timestamp}',
        'executables': [
            {
                'executable': '{path}',
                'runtime': '{seconds}',
                'memory': {MB},
                'cpu': {ms},
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
    old_times = int(time.time() - MAX_CONSOLE_PAGE_AGE)

    timestamp = datetime.datetime.utcfromtimestamp(
        jsondoc['started'])

    supervisor_model = models.Supervisor(
        hostname=jsondoc['host'],
        watch_dir=jsondoc['watch_dir'],
        started=timestamp
    )

    supervisor_model = db.session.merge(supervisor_model)

    autoincrement(supervisor_model, models.Supervisor)

    for executable in jsondoc['executables']:

        process_model = models.Process(
            path=executable['executable'],
            supervisor_id=supervisor_model.id
        )

        process_model = db.session.merge(process_model)

        autoincrement(process_model, models.Process)

        process_model.runtime = process_model.runtime or 0
        process_model.runtime += executable['runtime']

        process_model.memory = executable['memory']

        process_model.cpu = process_model.cpu or 0
        process_model.cpu += executable['cpu']

        process_model.files = executable['files']

        process_model.exits = process_model.exits or 0
        process_model.exits += executable['exits']

        process_model.changes = process_model.changes or 0
        process_model.changes += executable['changes']

        process_model.update_interval = (
                jsondoc['last_update'] - jsondoc['first_update'])

        timestamp = datetime.datetime.utcfromtimestamp(
            jsondoc['last_update'])

        process_model.last_update = timestamp

        query = (
            models.Endpoint
            .query
            .filter_by(process_id=process_model.id))

        existing_endpoints = set(
            (x.protocol, x.address) for x in query.all())

        reported_endpoints = set()

        for protocol, addresses in executable['endpoints'].items():
            for address in addresses:
                reported_endpoints.add((protocol, address))

        new_endpoints = reported_endpoints.difference(existing_endpoints)

        for protocol, address in new_endpoints:
            endpoint_model = models.Endpoint(
                protocol=protocol,
                address=address,
                process_id=process_model.id
            )

            autoincrement(endpoint_model, models.Endpoint)
            db.session.add(endpoint_model)

        removed_endpoints = existing_endpoints.difference(reported_endpoints)

        for protocol, address in removed_endpoints:
            query = (
                db.session
                .query(models.Endpoint)
                .filter_by(protocol=protocol)
                .filter_by(address=address)
                .filter_by(process_id=process_model.id))

            query.delete()

        query = (
            db.session
            .query(models.ConsolePage)
            .filter(models.ConsolePage.process_id == process_model.id)
            .filter(models.ConsolePage.timestamp < old_times)
        )

        query.delete()

        for console_page in executable['console']:

            timestamp = datetime.datetime.utcfromtimestamp(
                console_page['timestamp'])

            console_page_model = models.ConsolePage(
                timestamp=timestamp,
                text=console_page['text'],
                process_id=process_model.id
            )

            autoincrement(console_page_model, models.ConsolePage)

            db.session.add(console_page_model)

        db.session.commit()
