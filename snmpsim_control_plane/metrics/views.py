#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator metrics: REST API views
#
import flask
from werkzeug import exceptions
from sqlalchemy import func

from snmpsim_control_plane.metrics import app
from snmpsim_control_plane.metrics import models
from snmpsim_control_plane.metrics import schemas

PREFIX = '/snmpsim/metrics/v1'


@app.errorhandler(exceptions.HTTPException)
def flask_exception_handler(exc):
    app.logger.error(exc)
    err = {
        'status': exc.code,
        'message': exc.description
    }
    response = flask.jsonify(err)
    response.status_code = exc.code
    return response


@app.errorhandler(Exception)
def all_exception_handler(exc):
    app.logger.error(exc)
    err = {
        'status': 400,
        'message': getattr(exc, 'message', str(exc))
    }
    response = flask.jsonify(err)
    response.status_code = 400
    return response


PACKETS_QS_COLUMN_MAP = {
    'protocol': models.Transport.transport_protocol,
    'local_address': models.Transport.endpoint,
    'peer_address': models.Transport.peer,
}

MESSAGES_QS_COLUMN_MAP = {
    'engine_id': models.Agent.engine,
    'security_model': models.Agent.security_model,
    'security_level': models.Agent.security_level,
    'context_engine_id': models.Agent.context_engine,
    'context_name': models.Agent.context_name,
    'pdu_type': models.Pdu.name,
    'recording': models.Recording.path,
}

QS_COLUMN_MAP = PACKETS_QS_COLUMN_MAP.copy()
QS_COLUMN_MAP.update(MESSAGES_QS_COLUMN_MAP)


def filter_by(query, *fields):
    search_columns = flask.request.args

    unknown_columns = set(search_columns).difference(fields)
    if unknown_columns:
        raise exceptions.NotFound(
            'Search term(s) %s not supported' % ', '.join(unknown_columns))

    for field in fields:
        args = search_columns.getlist(field)
        if args:
            query = query.filter(
                QS_COLUMN_MAP[field].in_(args))

    return query


@app.route(PREFIX + '/')
def show_root():
    return {
        'activity': flask.url_for('show_activity')
    }


@app.route(PREFIX + '/activity')
def show_activity():
    return {
        'packets': flask.url_for('show_packets'),
        'messages': flask.url_for('show_messages')
    }


def _make_filter_hyperlinks(target):
    return {
        flt: {
            'self': {
                '_links': flask.url_for('show_filter', target=target, flt=flt)
            }
        }
        for flt in (PACKETS_QS_COLUMN_MAP
                    if target == 'packets' else QS_COLUMN_MAP)
    }


@app.route(PREFIX + '/activity/packets/filters')
def show_packets_filters():
    return _make_filter_hyperlinks(target='packets')


@app.route(PREFIX + '/activity/messages/filters')
def show_messages_filters():
    return _make_filter_hyperlinks(target='messages')


@app.route(PREFIX + '/activity/<target>/filters/<flt>')
def show_filter(target, flt):
    try:
        column = (PACKETS_QS_COLUMN_MAP
                  if target == 'packets' else QS_COLUMN_MAP)[flt]

    except KeyError:
        raise exceptions.NotFound('No such filter')

    metrics = (
        models.Transport
        .query
        .with_entities(column)
        .group_by(column)
        .all())

    return flask.jsonify([mtr[0] for mtr in metrics])


def _show_packets_or_messages(show_messages=False):
    transport_query = (
        models.Transport
        .query
        .with_entities(
            func.sum(models.Packet.total).label("total"),
            func.sum(models.Packet.parse_failures).label("parse_failures"),
            func.sum(models.Packet.auth_failures).label("auth_failures"),
            func.sum(models.Packet.context_failures).label("context_failures")))

    # We have to build JSON response by hand because here it's a mix of
    # ORM models and custom dicts. Marshmallow does not seem to be well-suited
    # for handling that.
    metrics = {}

    if show_messages:
        agent_query = (
            transport_query
            .join(models.Transport)
            .join(models.Agent)
            .join(models.Recording)
            .join(models.Pdu))

        agent_query = filter_by(agent_query, *QS_COLUMN_MAP)

        var_binds_query = (
            agent_query
            .join(models.VarBind)
            .with_entities(
                func.sum(models.Pdu.total).label("pdus"),
                func.sum(models.VarBind.total).label("var_binds"),
                func.sum(models.VarBind.failures).label("failures")))

        variations_query = (
            agent_query
            .join(models.Variation)
            .with_entities(
                models.Variation.name,
                func.sum(models.Variation.total).label("total"),
                func.sum(models.Variation.failures).label("failures"))
            .group_by(models.Variation.name))

        messages = var_binds_query.first()
        schema = schemas.MessagesSchema()
        messages = schema.dump(messages).data

        variations = variations_query.all()
        schema = schemas.VariationsSchema(many=True)
        variations = schema.dump(variations).data

        _self = flask.url_for(
            'show_messages', **dict(
                (field, flask.request.args.getlist(field))
                for field in QS_COLUMN_MAP))

        links = {
            'self': _self
        }

        filters = {
            '_links': {
                'self': flask.url_for('show_messages_filters')
            }
        }

        metrics.update(
            variations=variations, _links=links, filters=filters, **messages)

    else:
        transport_query = filter_by(transport_query, *PACKETS_QS_COLUMN_MAP)

        packets = transport_query.first()
        schema = schemas.PacketsSchema()
        packets = schema.dump(packets).data

        _self = flask.url_for(
            'show_packets', **dict(
                (field, flask.request.args.getlist(field))
                for field in PACKETS_QS_COLUMN_MAP))

        links = {
            'self': _self
        }

        filters = {
            '_links': {
                'self': flask.url_for('show_packets_filters')
            }
        }

        metrics.update(_links=links, filters=filters, **packets)

    return metrics


@app.route(PREFIX + '/activity/packets')
def show_packets():
    return _show_packets_or_messages(show_messages=False)


@app.route(PREFIX + '/activity/messages')
def show_messages():
    return _show_packets_or_messages(show_messages=True)


@app.route(PREFIX + '/processes')
@app.route(PREFIX + '/processes/<id>')
@app.route(PREFIX + '/supervisors/<supervisor_id>/processes')
def show_processes(id=None, supervisor_id=None):
    process_query = (
        models.Process
        .query
        .outerjoin(models.Endpoint)
        .outerjoin(models.ConsolePage))

    if supervisor_id is not None:
        process_query = (
            process_query
            .filter(models.Process.supervisor_id == supervisor_id))

    if id is None:
        processes = process_query.all()

    else:
        process_query = (
            process_query
            .filter(models.Process.id == id))

        processes = process_query.first()

        if not processes:
            raise exceptions.NotFound('Process not found')

    schema = schemas.ProcessSchema(many=id is None)
    return schema.jsonify(processes), 200


@app.route(PREFIX + '/supervisors')
@app.route(PREFIX + '/supervisors/<id>')
def show_supervisors(id=None):
    supervisor_query = (
        models.Supervisor
        .query
        .outerjoin(models.Process))

    if id is None:
        supervisors = supervisor_query.all()

    else:
        supervisor_query = (
            supervisor_query
            .filter(models.Supervisor.id == id))

        supervisors = supervisor_query.first()

        if not supervisors:
            raise exceptions.NotFound('Supervisor not found')

    schema = schemas.SupervisorSchema(many=id is None)
    return schema.jsonify(supervisors), 200


@app.route(PREFIX + '/endpoints')
@app.route(PREFIX + '/endpoints/<endpoint_id>')
@app.route(PREFIX + '/processes/<id>/endpoints')
@app.route(PREFIX + '/processes/<id>/endpoints/<endpoint_id>')
def show_endpoints(id=None, endpoint_id=None):
    endpoint_query = (
        models.Endpoint
        .query
        .join(models.Process))

    if id is not None:
        endpoint_query = (
            endpoint_query
            .filter(models.Process.id == id))

    if endpoint_id is None:
        endpoints = endpoint_query.all()

    else:
        endpoint_query = (
            endpoint_query
            .filter(models.Endpoint.id == id))

        endpoints = endpoint_query.first()

        if not endpoints:
            raise exceptions.NotFound('Endpoint not found')

    schema = schemas.EndpointSchema(many=endpoint_id is None)
    return schema.jsonify(endpoints), 200


@app.route(PREFIX + '/consoles/<id>')
@app.route(PREFIX + '/consoles/<id>/page/<page_id>')
@app.route(PREFIX + '/processes/<id>/console')
@app.route(PREFIX + '/processes/<id>/console/<page_id>')
def show_console(id, page_id=None):
    console_query = (
        models.ConsolePage
        .query
        .join(models.Process)
        .filter(models.Process.id == id)
        .order_by(models.ConsolePage.timestamp.asc()))

    if page_id is None:
        pages = console_query.all()

    else:
        console_query = (
            console_query
            .filter(models.ConsolePage.id == page_id))

        pages = console_query.first()

        if not pages:
            raise exceptions.NotFound('Console page not found')

    schema = schemas.ConsoleSchema(many=page_id is None)
    return schema.jsonify(pages), 200
