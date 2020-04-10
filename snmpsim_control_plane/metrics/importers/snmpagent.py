#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator metrics: snmpsim metrics importer
#
from snmpsim_control_plane.metrics import db
from snmpsim_control_plane.metrics import models
from snmpsim_control_plane.metrics.utils import autoincrement


def import_metrics(fulljson):
    """Update metrics DB from `dict` data structure.

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
    for tr_proto, tr_endpoints in fulljson.items():

        if not isinstance(tr_endpoints, dict):
            continue

        for tr_endpoint, peers in tr_endpoints.items():

            if not isinstance(peers, dict):
                continue

            for peer_adddress, engines in peers.items():

                if not isinstance(engines, dict):
                    continue

                tr_mdl = models.Transport(
                    transport_protocol=tr_proto,
                    endpoint=tr_endpoint,
                    peer=peer_adddress,
                )

                tr_mdl = db.session.merge(tr_mdl)

                autoincrement(tr_mdl, models.Transport)

                packet_mdl = models.Packet(
                    transport_id=tr_mdl.id)

                packet_mdl = db.session.merge(packet_mdl)

                packet_mdl.total = packet_mdl.total or 0
                packet_mdl.total += engines['packets']

                packet_mdl.parse_failures = packet_mdl.parse_failures or 0
                packet_mdl.parse_failures += engines['parse_failures']

                packet_mdl.auth_failures = packet_mdl.auth_failures or 0
                packet_mdl.auth_failures += engines['auth_failures']

                packet_mdl.context_failures = (
                    packet_mdl.context_failures or 0)
                packet_mdl.context_failures += engines['context_failures']

                for engine_id, security_models in engines.items():
                    if not isinstance(security_models, dict):
                        continue

                    for security_model, security_levels in (
                            security_models.items()):
                        if not isinstance(security_levels, dict):
                            continue

                        for security_level, context_engines in (
                                security_levels.items()):
                            if not isinstance(context_engines, dict):
                                continue

                            for ctx_engine_id, ctx_names in (
                                    context_engines.items()):
                                if not isinstance(ctx_names, dict):
                                    continue

                                for context_name, pdus in (
                                        ctx_names.items()):
                                    if not isinstance(pdus, dict):
                                        continue

                                    for pdu_type, recordings in pdus.items():
                                        if not isinstance(recordings, dict):
                                            continue

                                        for recording, counters in (
                                                recordings.items()):
                                            agent_mdl = models.Agent(
                                                transport_id=tr_mdl.id,
                                                engine=engine_id,
                                                security_model=security_model,
                                                security_level=security_level,
                                                context_engine=ctx_engine_id,
                                                context_name=context_name,
                                            )

                                            agent_mdl = db.session.merge(
                                                agent_mdl)

                                            autoincrement(
                                                agent_mdl, models.Agent)

                                            recording_mdl = models.Recording(
                                                agent_id=agent_mdl.id,
                                                path=recording)

                                            recording_mdl = db.session.merge(
                                                recording_mdl)

                                            autoincrement(
                                                recording_mdl,
                                                models.Recording)

                                            pdu_mdl = models.Pdu(
                                                recording_id=recording_mdl.id,
                                                name=pdu_type)

                                            pdu_mdl = db.session.merge(
                                                pdu_mdl)

                                            pdu_mdl.total = (
                                                pdu_mdl.total or 0)
                                            pdu_mdl.total += counters['pdus']

                                            autoincrement(
                                                pdu_mdl, models.Pdu)

                                            varbind_mdl = models.VarBind(
                                                pdu_id=pdu_mdl.id)

                                            varbind_mdl = db.session.merge(
                                                varbind_mdl)

                                            varbind_mdl.total = (
                                                varbind_mdl.total or 0)
                                            varbind_mdl.total += (
                                                counters['varbinds'])

                                            varbind_mdl.failures = (
                                                varbind_mdl.failures or 0)
                                            varbind_mdl.failures += (
                                                counters['failures'])

                                            variations = counters.get(
                                                'variations', ())

                                            for name, counters in (
                                                variations.items()):

                                                vartn_mdl = models.Variation(
                                                    pdu_id=pdu_mdl.id,
                                                    name=name)

                                                vartn_mdl = (
                                                    db.session.merge(
                                                        vartn_mdl))

                                                vartn_mdl.total = (
                                                    vartn_mdl.total or 0)
                                                vartn_mdl.total += (
                                                    counters['calls'])

                                                vartn_mdl.failures = (
                                                    vartn_mdl.failures or 0)
                                                vartn_mdl.failures += (
                                                    counters['failures'])

                                            db.session.commit()
