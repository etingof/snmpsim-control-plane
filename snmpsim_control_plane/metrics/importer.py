#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator metrics: ORM models importer
#
from sqlalchemy import func

from snmpsim_control_plane.metrics import db
from snmpsim_control_plane.metrics import models


def autoincrement(obj, model):
    """Add unique ID to model.

    Sqlalchemy's merge requires unique fields being primary keys. On top of
    that, autoincrement does not always work with Sqlalchemy. Thus this
    hack to generate unique row ID. %-(
    """
    if obj.id is None:
        max_id = db.session.query(func.max(model.id)).first()
        max_id = max_id[0]
        max_id = max_id + 1 if max_id else 1
        obj.id = max_id

        db.session.commit()


def import_metrics(fulljson):
    """Update metrics DB from `dict` data structure

    The input data structure is expected to be the one produced by SNMP
    simulator's command responder `fulljson` reporting module.


    .. code-block:: python

    {
        'format': 'fulljson',
        'version': 1,
        'producer': <UUID>,
        'first_update': '{timestamp}',
        'last_update': '{timestamp}',
        '{transport_protocol}': {
            '{transport_endpoint}': {  # local address
                'transport_domain': '{transport_domain}',  # endpoint ID
                '{transport_address}', { # peer address
                    'packets': 0,
                    'parse_failures': 0,  # n/a
                    'auth_failures': 0,  # n/a
                    'context_failures': 0, # n/a
                    '{snmp_engine}': {
                        '{security_model}': {
                            '{security_level}': {
                                '{security_name}': {
                                    '{context_engine_id}': {
                                        '{context_name}': {
                                            '{pdu_type}': {
                                                '{data_file}': {
                                                    'pdus': 0,
                                                    'varbinds': 0,
                                                    'failures': 0,
                                                    '{variation_module}': {
                                                        'calls': 0,
                                                        'failures': 0
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """

    for transport_protocol, transport_endpoints in fulljson.items():

        if not isinstance(transport_endpoints, dict):
            continue

        for transport_endpoint, peers in transport_endpoints.items():

            if not isinstance(peers, dict):
                continue

            for peer_adddress, engines in peers.items():

                if not isinstance(engines, dict):
                    continue

                transport_model = models.Transport(
                    transport_protocol=transport_protocol,
                    endpoint=transport_endpoint,
                    peer=peer_adddress,
                )

                transport_model = db.session.merge(transport_model)

                autoincrement(transport_model, models.Transport)

                packet_model = models.Packet(
                    transport_id=transport_model.id)

                packet_model = db.session.merge(packet_model)

                packet_model.total = packet_model.total or 0
                packet_model.total += engines['packets']

                packet_model.parse_failures = packet_model.parse_failures or 0
                packet_model.parse_failures += engines['parse_failures']

                packet_model.auth_failures = packet_model.auth_failures or 0
                packet_model.auth_failures += engines['auth_failures']

                packet_model.context_failures = packet_model.context_failures or 0
                packet_model.context_failures += engines['context_failures']

                for engine_id, security_models in engines.items():
                    if not isinstance(security_models, dict):
                        continue

                    for security_model, security_levels in security_models.items():
                        if not isinstance(security_levels, dict):
                            continue

                        for security_level, context_engines in security_levels.items():
                            if not isinstance(context_engines, dict):
                                continue

                            for context_engine_id, context_names in context_engines.items():
                                if not isinstance(context_names, dict):
                                    continue

                                for context_name, pdus in context_names.items():
                                    if not isinstance(pdus, dict):
                                        continue

                                    for pdu_type, recordings in pdus.items():
                                        if not isinstance(recordings, dict):
                                            continue

                                        for recording, counters in recordings.items():
                                            agent_model = models.Agent(
                                                transport_id=transport_model.id,
                                                engine=engine_id,
                                                security_model=security_model,
                                                security_level=security_level,
                                                context_engine=context_engine_id,
                                                context_name=context_name,
                                            )

                                            agent_model = db.session.merge(agent_model)

                                            autoincrement(agent_model, models.Agent)

                                            recording_model = models.Recording(
                                                agent_id=agent_model.id, path=recording)

                                            recording_model = db.session.merge(recording_model)

                                            autoincrement(recording_model, models.Recording)

                                            pdu_model = models.Pdu(
                                                recording_id=recording_model.id, name=pdu_type)

                                            pdu_model = db.session.merge(pdu_model)

                                            pdu_model.total = pdu_model.total or 0
                                            pdu_model.total += counters['pdus']

                                            autoincrement(pdu_model, models.Pdu)

                                            varbind_model = models.VarBind(pdu_id=pdu_model.id)

                                            varbind_model = db.session.merge(varbind_model)

                                            varbind_model.total = varbind_model.total or 0
                                            varbind_model.total += counters['varbinds']

                                            varbind_model.failures = varbind_model.failures or 0
                                            varbind_model.failures += counters['failures']

                                            variations = counters.get('variations', ())

                                            for name, counters in variations.items():

                                                variation_model = models.Variation(
                                                    pdu_id=pdu_model.id, name=name)

                                                variation_model = db.session.merge(variation_model)

                                                variation_model.total = variation_model.total or 0
                                                variation_model.total += counters['calls']

                                                variation_model.failures = variation_model.failures or 0
                                                variation_model.failures += counters['failures']

                                            db.session.commit()
