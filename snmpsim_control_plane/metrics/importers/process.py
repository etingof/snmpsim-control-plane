#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator metrics: supervisor metrics importer
#
from snmpsim_control_plane.metrics import db
from snmpsim_control_plane.metrics import models
from snmpsim_control_plane.metrics.utils import autoincrement


MAX_CONSOLE_PAGES = 50


def import_metrics(jsondoc):
    """Update metrics DB from `dict` data structure

    The input data structure is expected to be the one produced by SNMP
    simulator's command responder `fulljson` reporting module.



    .. code-block:: python

    {
        'format': 'jsondoc',
        'version': 1,
        'host': '{hostname}',
        'producer': <UUID>,
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
                        'page': 0,
                        'timestamp': 0,
                        'text': '{text}'
                    }
                ]
            }
        ]
    }
    """
    supervisor_model = models.Supervisor(
        hostname=jsondoc['host'],
        producer=jsondoc['producer']
    )

    supervisor_model = db.session.merge(supervisor_model)

    autoincrement(supervisor_model, models.Supervisor)

    for executable in jsondoc['executables']:

        executable_model = models.Executable(
            path=executable['executable'],
            supervisor_id=supervisor_model.id
        )

        executable_model = db.session.merge(executable_model)

        autoincrement(executable_model, models.Executable)

        process_model = models.Process(
            executable_id=executable_model.id
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

        process_model.last_update = jsondoc['last_update']

        query = (
            models.Endpoint
            .query
            .filter_by(process_id=process_model.id)
        )
        query.delete()

        for protocol, addresses in executable['endpoints']:

            for address in addresses:
                endpoint_model = models.Endpoint(
                    protocol=protocol,
                    address=address,
                    process_id=process_model.id
                )

                db.session.add(endpoint_model)

        query = (
            models.ConsolePage
            .query
            .filter_by(process_id=process_model.id)
            .order_by(models.ConsolePage.timestamp.asc())
        )
        console_pages_count = query.count()

        while console_pages_count > MAX_CONSOLE_PAGES:
            console_page = query.first()
            db.session.delete(console_page)
            console_pages_count -= 1

        for console_page in executable['console']:

            console_page_model = models.ConsolePage(
                page=console_page['page'],
                timestamp=console_page['timestamp'],
                text=console_page['text'],
                process_id=process_model.id
            )

            db.session.add(console_page_model)

        db.session.commit()
