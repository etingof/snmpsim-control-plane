#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator management: REST API views
#
import os
import tempfile
from functools import wraps

import flask
from sqlalchemy import func
from werkzeug import exceptions

from snmpsim_control_plane import error
from snmpsim_control_plane.management import app
from snmpsim_control_plane.management import db
from snmpsim_control_plane.management import models
from snmpsim_control_plane.management import recording
from snmpsim_control_plane.management import schemas
from snmpsim_control_plane.management.exporters import builder
from snmpsim_control_plane.management.exporters import renderer

PREFIX = '/snmpsim/mgmt/v1'
TARGET_CONFIG = 'snmpsim-run-labs.sh'


def render_config(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)

        context = builder.to_dict()

        template = app.config['SNMPSIM_MGMT_TEMPLATE']
        dst = os.path.join(
            app.config['SNMPSIM_MGMT_DESTINATION'],
            TARGET_CONFIG)

        renderer.render_configuration(dst, template, context)

        return response

    return decorated_function


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


def cleanup_recordings(f):
    @wraps(f)
    def rm_empty_dirs(top_dir, delete=False):
        entries = os.listdir(top_dir)

        for entry in entries:
            sub_dir = os.path.join(top_dir, entry)
            if not os.path.isdir(sub_dir):
                continue

            rm_empty_dirs(sub_dir, delete=True)

        if delete:
            try:
                os.rmdir(top_dir)

            except OSError:
                return

    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)

        rm_empty_dirs(app.config['SNMPSIM_MGMT_DATAROOT'])

        return response

    return decorated_function


def search_model(model, query):

    known_columns = model.__table__.columns.keys()

    for search_column in flask.request.args:
        if search_column not in known_columns:
            raise exceptions.NotFound(
                'Search term %s is not supported' % search_column)

        search_terms = flask.request.args.getlist(search_column)
        if search_terms:
            search_terms = [term.lower() for term in search_terms]
            query = query.filter(
                func.lower(getattr(model, search_column)).in_(search_terms))

    return query


@app.route(PREFIX + '/endpoints')
def show_endpoints():
    endpoints_query = (
        models.Endpoint
        .query
        .outerjoin(models.EngineEndpoint)
        .outerjoin(models.Engine))

    endpoints_query = search_model(models.Endpoint, endpoints_query)

    schema = schemas.EndpointSchema(many=True)
    return schema.jsonify(endpoints_query.all())


@app.route(PREFIX + '/endpoints/<id>', methods=['GET'])
def show_endpoint(id):
    endpoint = (
        models.Endpoint
        .query
        .filter_by(id=id)
        .outerjoin(models.EngineEndpoint)
        .outerjoin(models.Engine)
        .first())

    if not endpoint:
        raise exceptions.NotFound('Endpoint not found')

    schema = schemas.EndpointSchema()
    return schema.jsonify(endpoint), 200


@app.route(PREFIX + '/endpoints', methods=['POST'])
@app.route(PREFIX + '/tags/<tag_id>/endpoint', methods=['POST'])
@render_config
def new_endpoint(tag_id=None):
    req = flask.request.json

    endpoint = models.Endpoint(**req)
    db.session.add(endpoint)

    if tag_id:
        db.session.flush()
        tag_endpoint = models.TagEndpoint(
            tag_id=tag_id, endpoint_id=endpoint.id)
        db.session.add(tag_endpoint)

    db.session.commit()

    schema = schemas.EndpointSchema()
    return schema.jsonify(endpoint), 201


@app.route(PREFIX + '/endpoints/<id>', methods=['DELETE'])
@render_config
def del_endpoint(id):
    endpoint = (
        models.Endpoint
        .query
        .filter_by(id=id)
        .first())

    if not endpoint:
        raise exceptions.NotFound('Endpoint not found')

    db.session.delete(endpoint)
    db.session.commit()

    return flask.Response(status=204)


@app.route(PREFIX + '/users')
def show_users():
    users_query = (
        models.User
        .query)

    users_query = search_model(models.User, users_query)

    schema = schemas.UserSchema(many=True)
    return schema.jsonify(users_query.all()), 200


@app.route(PREFIX + '/users/<id>', methods=['GET'])
def show_user(id):
    user = (
        models.User
        .query
        .filter_by(id=id)
        .first())

    if not user:
        raise exceptions.NotFound('User not found')

    schema = schemas.UserSchema()
    return schema.jsonify(user), 200


@app.route(PREFIX + '/users', methods=['POST'])
@app.route(PREFIX + '/tags/<tag_id>/user', methods=['POST'])
@render_config
def new_user(tag_id=None):
    req = flask.request.json

    user = models.User(**req)
    db.session.add(user)

    if tag_id:
        db.session.flush()
        tag_user = models.TagUser(
            tag_id=tag_id, user_id=user.id)
        db.session.add(tag_user)

    db.session.commit()

    schema = schemas.UserSchema()
    return schema.jsonify(user), 201


@app.route(PREFIX + '/users/<id>', methods=['DELETE'])
@render_config
def del_user(id):
    user = (
        models.User
        .query
        .filter_by(id=id)
        .first())

    if not user:
        raise exceptions.NotFound('User not found')

    db.session.delete(user)
    db.session.commit()

    return flask.Response(status=204)


@app.route(PREFIX + '/engines')
def show_engines():
    engines_query = (
        models.Engine
        .query
        .outerjoin(models.EngineUser)
        .outerjoin(models.User))

    engines_query = search_model(models.Engine, engines_query)

    schema = schemas.EngineSchema(many=True)
    return schema.jsonify(engines_query.all()), 200


@app.route(PREFIX + '/engines/<id>', methods=['GET'])
def show_engine(id):
    engine = (
        models.Engine
        .query
        .filter_by(id=id)
        .outerjoin(models.EngineUser)
        .outerjoin(models.User)
        .first())

    if not engine:
        return flask.make_response('Engine not found', 404)

    schema = schemas.EngineSchema()
    return schema.jsonify(engine), 200


@app.route(PREFIX + '/engines', methods=['POST'])
@app.route(PREFIX + '/tags/<tag_id>/engine', methods=['POST'])
@render_config
def new_engine(tag_id=None):
    req = flask.request.json

    engine = models.Engine(**req)
    db.session.add(engine)

    if tag_id:
        db.session.flush()
        tag_engine = models.TagEngine(
            tag_id=tag_id, engine_id=engine.id)
        db.session.add(tag_engine)

    db.session.commit()

    schema = schemas.EngineSchema()
    return schema.jsonify(engine), 201


@app.route(PREFIX + '/engines/<id>', methods=['DELETE'])
@render_config
def del_engine(id):
    engine = (
        models
        .Engine
        .query
        .filter_by(id=id)
        .first())

    if not engine:
        raise exceptions.NotFound('Engine not found')

    db.session.delete(engine)
    db.session.commit()

    return flask.Response(status=204)


@app.route(PREFIX + '/engines/<id>/user/<user_id>', methods=['PUT'])
@render_config
def add_engine_user(id, user_id):
    engine_user = models.EngineUser(user_id=user_id, engine_id=id)

    db.session.add(engine_user)
    db.session.commit()

    engine = models.Engine.query.filter_by(id=id).first()
    schema = schemas.EngineSchema()
    return schema.jsonify(engine), 200


@app.route(PREFIX + '/engines/<id>/user/<user_id>', methods=['DELETE'])
@render_config
def del_engine_user(id, user_id):
    engine_user = (
        models
        .EngineUser
        .query
        .filter_by(engine_id=id, user_id=user_id)
        .first())

    if not engine_user:
        raise exceptions.NotFound('Engine <-> user binding not found')

    db.session.delete(engine_user)
    db.session.commit()

    engine = models.Engine.query.filter_by(id=id).first()
    schema = schemas.EngineSchema()
    return schema.jsonify(engine), 204


@app.route(PREFIX + '/engines/<id>/endpoint/<endpoint_id>', methods=['PUT'])
@render_config
def add_engine_endpoint(id, endpoint_id):
    engine_endpoint = models.EngineEndpoint(
        endpoint_id=endpoint_id, engine_id=id)

    db.session.add(engine_endpoint)
    db.session.commit()

    engine = (
        models
        .Engine
        .query
        .filter_by(id=id).first())

    schema = schemas.EngineSchema()
    return schema.jsonify(engine), 200


@app.route(PREFIX + '/engines/<id>/endpoint/<endpoint_id>', methods=['DELETE'])
@render_config
def del_engine_endpoint(id, endpoint_id):
    engine_endpoint = (
        models
        .EngineEndpoint
        .query
        .filter_by(engine_id=id, endpoint_id=endpoint_id).first())

    if not engine_endpoint:
        raise exceptions.NotFound('Engine <-> endpoint binding not found')

    db.session.delete(engine_endpoint)
    db.session.commit()

    engine = models.Engine.query.filter_by(id=id).first()
    schema = schemas.EngineSchema()

    return schema.jsonify(engine), 204


@app.route(PREFIX + '/agents')
def show_agents():
    agents_query = (
        models.Agent
        .query
        .outerjoin(models.AgentEngine)
        .outerjoin(models.Engine))

    agents_query = search_model(models.Agent, agents_query)

    schema = schemas.AgentSchema(many=True)
    return schema.jsonify(agents_query.all()), 200


@app.route(PREFIX + '/agents/<id>', methods=['GET'])
def show_agent(id):
    agent = (
        models.Agent
        .query
        .filter_by(id=id)
        .outerjoin(models.AgentEngine)
        .outerjoin(models.Engine)
        .first())

    if not agent:
        raise exceptions.NotFound('Agent not found')

    schema = schemas.AgentSchema()
    return schema.jsonify(agent), 200


@app.route(PREFIX + '/agents', methods=['POST'])
@app.route(PREFIX + '/tags/<tag_id>/agent', methods=['POST'])
@render_config
def new_agent(tag_id=None):
    req = flask.request.json

    data_dir = req.get('data_dir')
    if data_dir:
        data_dir = os.path.join(
            app.config['SNMPSIM_MGMT_DATAROOT'],
            data_dir)

        data_dir = os.path.abspath(data_dir)

        if not data_dir.startswith(
                os.path.abspath(app.config['SNMPSIM_MGMT_DATAROOT'])):
            raise error.ControlPlaneError(
                'Data directory outside of data root: %s' % data_dir)

        req.update(data_dir=data_dir)

    agent = models.Agent(**req)
    db.session.add(agent)

    if tag_id:
        db.session.flush()
        tag_agent = models.TagAgent(
            tag_id=tag_id, agent_id=agent.id)
        db.session.add(tag_agent)

    db.session.commit()

    schema = schemas.AgentSchema()
    return schema.jsonify(agent), 201


@app.route(PREFIX + '/agents/<id>', methods=['DELETE'])
@render_config
def del_agent(id):
    agent = (
        models
        .Agent
        .query
        .filter_by(id=id)
        .first())

    if not agent:
        raise exceptions.NotFound('Agent not found')

    db.session.delete(agent)
    db.session.commit()

    return flask.Response(status=204)


@app.route(PREFIX + '/agents/<id>/engine/<engine_id>', methods=['PUT'])
@render_config
def add_agent_engine(id, engine_id):
    agent_engine = (
        models
        .AgentEngine(agent_id=id, engine_id=engine_id))

    db.session.add(agent_engine)
    db.session.commit()

    agent = (
        models
        .Agent
        .query
        .filter_by(id=id).first())

    schema = schemas.AgentSchema()
    return schema.jsonify(agent), 200


@app.route(PREFIX + '/agents/<id>/engine/<engine_id>', methods=['DELETE'])
@render_config
def del_agent_engine(id, engine_id):
    agent_engine = (
        models
        .AgentEngine
        .query
        .filter_by(engine_id=engine_id, agent_id=id).first())

    if not agent_engine:
        raise exceptions.NotFound('Agent <-> engine binding not found')

    db.session.delete(agent_engine)
    db.session.commit()

    agent = (
        models
        .Agent
        .query
        .filter_by(id=id).first())

    schema = schemas.AgentSchema()
    return schema.jsonify(agent), 204


@app.route(PREFIX + '/selectors')
def show_selectors():
    selectors_query = (
        models.Selector
        .query
        .outerjoin(models.AgentSelector)
        .outerjoin(models.Agent))

    selectors_query = search_model(models.Selector, selectors_query)

    schema = schemas.SelectorSchema(many=True)
    return schema.jsonify(selectors_query.all()), 200


@app.route(PREFIX + '/selectors/<id>', methods=['GET'])
def show_selector(id):
    selector_query = (
        models.Selector
        .query
        .filter_by(id=id)
        .outerjoin(models.AgentSelector)
        .outerjoin(models.Agent)
        .first())

    if not selector_query:
        raise exceptions.NotFound('Selector not found')

    schema = schemas.SelectorSchema()
    return schema.jsonify(selector_query), 200


@app.route(PREFIX + '/selectors', methods=['POST'])
@app.route(PREFIX + '/tags/<tag_id>/selector', methods=['POST'])
@render_config
def new_selector(tag_id=None):
    req = flask.request.json

    selector = models.Selector(**req)
    db.session.add(selector)

    if tag_id:
        db.session.flush()
        tag_selector = models.TagSelector(
            tag_id=tag_id, selector_id=selector.id)
        db.session.add(tag_selector)

    db.session.commit()

    schema = schemas.SelectorSchema()
    return schema.jsonify(selector), 201


@app.route(PREFIX + '/selectors/<id>', methods=['DELETE'])
@render_config
def del_selector(id):
    selector = (
        models.Selector
        .query
        .filter_by(id=id)
        .first())

    if not selector:
        raise exceptions.NotFound('Selector not found')

    db.session.delete(selector)
    db.session.commit()

    return flask.Response(status=204)


@app.route(PREFIX + '/agents/<id>/selector/<selector_id>/<order>',
           methods=['PUT'])
@render_config
def add_agent_selector(id, selector_id, order):
    agent_selector = (
        models
        .AgentSelector(agent_id=id, selector_id=selector_id, order=order))

    db.session.add(agent_selector)
    db.session.commit()

    agent = (
        models
        .Agent
        .query
        .filter_by(id=id).first())

    schema = schemas.AgentSchema()
    return schema.jsonify(agent), 200


@app.route(PREFIX + '/agents/<id>/selector/<selector_id>', methods=['DELETE'])
@render_config
def del_agent_selector(id, selector_id):
    agent_selector = (
        models
        .AgentSelector
        .query
        .filter_by(selector_id=selector_id, agent_id=id).first())

    if not agent_selector:
        raise exceptions.NotFound('Agent <-> selector binding not found')

    db.session.delete(agent_selector)
    db.session.commit()

    agent = (
        models
        .Agent
        .query
        .filter_by(id=id).first())

    schema = schemas.AgentSchema()
    return schema.jsonify(agent), 204


@app.route(PREFIX + '/recordings')
def show_recordings():
    try:
        recordings = recording.list_recordings(
            app.config['SNMPSIM_MGMT_DATAROOT'])

    except error.ControlPlaneError:
        raise exceptions.NotFound('Recording not found')

    schema = schemas.RecordingSchema(many=True)
    return schema.jsonify(recordings), 200


@app.route(PREFIX + '/recordings/<path:path>', methods=['GET'])
def show_recording(path):
    try:
        directory, file = recording.get_recording(
            app.config['SNMPSIM_MGMT_DATAROOT'], path, exists=True)

    except error.ControlPlaneError:
        raise exceptions.NotFound('Recording not found')

    return flask.send_from_directory(directory, file)


@app.route(PREFIX + '/recordings/<path:path>', methods=['POST', 'PUT'])
def new_recording(path):
    recording_type = recording.get_recording_type(path)
    if not recording_type:
        raise error.ControlPlaneError('Unknown recording type')

    can_exist = flask.request.method == 'POST'

    try:
        directory, file = recording.get_recording(
            app.config['SNMPSIM_MGMT_DATAROOT'], path,
            not_exists=can_exist, ensure_path=True)

    except error.ControlPlaneError:
        raise exceptions.Conflict('Bad recording path (is it already exists?)')

    # TODO: is it a memory hog when .snmprec file is large?
    with tempfile.NamedTemporaryFile(dir=directory, delete=False) as fl:
        fl.write(flask.request.data)

    os.rename(fl.name, os.path.join(directory, file))

    return flask.Response(status=204)


@app.route(PREFIX + '/recordings/<path:path>', methods=['DELETE'])
@cleanup_recordings
def del_recording(path):
    try:
        directory, file = recording.get_recording(
            app.config['SNMPSIM_MGMT_DATAROOT'], path, exists=True)

    except error.ControlPlaneError:
        raise exceptions.NotFound('Recording not found')

    os.unlink(os.path.join(directory, file))

    return flask.Response(status=204)


@app.route(PREFIX + '/labs')
def show_labs():
    labs_query = (
        models.Lab
        .query
        .outerjoin(models.LabAgent)
        .outerjoin(models.Agent))

    labs_query = search_model(models.Lab, labs_query)

    schema = schemas.LabSchema(many=True)
    return schema.jsonify(labs_query.all()), 200


@app.route(PREFIX + '/labs/<id>', methods=['GET'])
def show_lab(id):
    lab = (
        models.Lab
        .query
        .filter_by(id=id)
        .outerjoin(models.LabAgent)
        .outerjoin(models.Agent)
        .first())

    if not lab:
        raise exceptions.NotFound('Lab not found')

    schema = schemas.LabSchema()
    return schema.jsonify(lab), 200


@app.route(PREFIX + '/labs', methods=['POST'])
@app.route(PREFIX + '/tags/<tag_id>/lab', methods=['POST'])
@render_config
def new_lab(tag_id=None):
    req = flask.request.json

    lab = models.Lab(**req)
    db.session.add(lab)

    if tag_id:
        db.session.flush()
        tag_lab = models.TagLab(
            tag_id=tag_id, lab_id=lab.id)
        db.session.add(tag_lab)

    db.session.commit()

    schema = schemas.LabSchema()
    return schema.jsonify(lab), 201


@app.route(PREFIX + '/labs/<id>', methods=['DELETE'])
@render_config
def del_lab(id):
    lab = (
        models
        .Lab
        .query
        .filter_by(id=id)
        .first())

    if not lab:
        raise exceptions.NotFound('Lab not found')

    db.session.delete(lab)
    db.session.commit()

    return flask.Response(status=204)


@app.route(PREFIX + '/labs/<id>/agent/<agent_id>', methods=['PUT'])
@render_config
def add_lab_agent(id, agent_id):
    lab_agent = models.LabAgent(agent_id=agent_id, lab_id=id)

    db.session.add(lab_agent)
    db.session.commit()

    lab = models.Lab.query.filter_by(id=id).first()

    schema = schemas.LabSchema()
    return schema.jsonify(lab), 200


@app.route(PREFIX + '/labs/<id>/agent/<agent_id>', methods=['DELETE'])
@render_config
def del_lab_agent(id, agent_id):
    lab_agent = (
        models
        .LabAgent
        .query
        .filter_by(agent_id=agent_id, lab_id=id)
        .first())

    if not lab_agent:
        raise exceptions.NotFound('Lab <-> agent binding not found')

    db.session.delete(lab_agent)
    db.session.commit()

    engine = models.Lab.query.filter_by(id=id).first()
    schema = schemas.LabSchema()
    return schema.jsonify(engine), 204


@app.route(PREFIX + '/labs/<id>/power/<state>', methods=['PUT'])
@render_config
def change_lab_power(id, state):
    lab = (
        models.Lab
        .query
        .filter_by(id=id)
        .first())

    if not lab:
        raise exceptions.NotFound('Lab not found')

    lab.power = state.lower()

    db.session.commit()

    lab = models.Lab.query.filter_by(id=id).first()

    schema = schemas.LabSchema()
    return schema.jsonify(lab), 200


def make_tags_query(tag_id=None):
    tags_query = (
        models.Tag
        .query)

    if tag_id is not None:
        tags_query = tags_query.filter_by(id=tag_id)

    tags_query = (
        tags_query
        .outerjoin(models.TagEndpoint)
        .outerjoin(models.Endpoint)
        .outerjoin(models.TagUser)
        .outerjoin(models.User)
        .outerjoin(models.TagEngine)
        .outerjoin(models.Engine)
        .outerjoin(models.TagSelector)
        .outerjoin(models.Selector)
        .outerjoin(models.TagAgent)
        .outerjoin(models.Agent)
        .outerjoin(models.TagLab)
        .outerjoin(models.Lab))

    return tags_query


@app.route(PREFIX + '/tags')
def show_tags():
    tags_query = make_tags_query()

    tags_query = search_model(models.Tag, tags_query)

    schema = schemas.TagSchema(many=True)
    return schema.jsonify(tags_query.all()), 200


@app.route(PREFIX + '/tags/<id>', methods=['GET'])
def show_tag(id):
    tags_query = make_tags_query(id)

    tag = tags_query.first()
    if not tag:
        raise exceptions.NotFound('Tag not found')

    schema = schemas.TagSchema()
    return schema.jsonify(tag), 200


@app.route(PREFIX + '/tags', methods=['POST'])
@render_config
def new_tag():
    req = flask.request.json

    tag = models.Tag(**req)
    db.session.add(tag)
    db.session.commit()

    tags_query = make_tags_query(tag.id)

    schema = schemas.TagSchema()
    return schema.jsonify(tags_query.first()), 201


@app.route(PREFIX + '/tags/<id>', methods=['DELETE'])
@render_config
def del_tag(id):
    tag_query = (
        models.Tag
        .query
        .filter_by(id=id))

    tag = tag_query.first()
    if not tag:
        raise exceptions.NotFound('Tag not found')

    db.session.delete(tag)
    db.session.commit()

    return flask.Response(status=204)


ENTITY_ADD_MAP = {
    'endpoint': lambda x, y: models.TagEndpoint(tag_id=x, endpoint_id=y),
    'user': lambda x, y: models.TagUser(tag_id=x, user_id=y),
    'engine': lambda x, y: models.TagEngine(tag_id=x, engine_id=y),
    'selector': lambda x, y: models.TagSelector(tag_id=x, selector_id=y),
    'agent': lambda x, y: models.TagAgent(tag_id=x, agent_id=y),
    'lab': lambda x, y: models.TagLab(tag_id=x, lab_id=y),
}


ENTITY_DEL_MAP = {
    'endpoint': lambda x, y: (
        models.TagEndpoint
        .query
        .filter_by(tag_id=x, endpoint_id=y)
    ),
    'user': lambda x, y: (
        models.TagUser
        .query
        .filter_by(tag_id=x, user_id=y)
    ),
    'engine': lambda x, y: (
        models.TagEngine
        .query
        .filter_by(tag_id=x, engine_id=y)
    ),
    'selector': lambda x, y: (
        models.TagSelector
        .query
        .filter_by(tag_id=x, selector_id=y)
    ),
    'agent': lambda x, y: (
        models
        .TagAgent
        .query
        .filter_by(tag_id=x, agent_id=y)
    ),
    'lab': lambda x, y: (
        models
        .TagLab
        .query
        .filter_by(tag_id=x, lab_id=y)
    ),
}


@app.route(PREFIX + '/tags/<id>/<entity>/<entity_id>', methods=['PUT'])
@render_config
def add_tag_entity(id, entity, entity_id):
    try:
        tag_entity = ENTITY_ADD_MAP[entity]

    except KeyError:
        raise exceptions.NotFound('Entity %s not found' % entity)

    tag_entity = tag_entity(id, entity_id)

    db.session.add(tag_entity)
    db.session.commit()

    tags_query = make_tags_query(id)

    schema = schemas.TagSchema()
    return schema.jsonify(tags_query.first()), 200


@app.route(PREFIX + '/tags/<id>/<entity>/<entity_id>', methods=['DELETE'])
@render_config
def del_tag_entity(id, entity, entity_id):
    try:
        entity_query = ENTITY_DEL_MAP[entity]

    except KeyError:
        raise exceptions.NotFound('Entity %s not found' % entity)

    entity_query = entity_query(id, entity_id)

    entity_instance = entity_query.first()

    if not entity_instance:
        raise exceptions.NotFound('Tag <-> %s binding not found' % entity)

    db.session.delete(entity_instance)
    db.session.commit()

    entity_query = make_tags_query(id)

    schema = schemas.TagSchema()
    return schema.jsonify(entity_query.first()), 200


DELETABLE_ENTITIES = (
    'endpoints', 'users', 'engines', 'selectors', 'agents', 'labs'
)


@app.route(PREFIX + '/tags/<id>/objects', methods=['DELETE'])
@render_config
def del_tagged_objects(id):
    tags_query = make_tags_query(id)

    tag = tags_query.first()
    if not tag:
        raise exceptions.NotFound('Tag with ID %s not found' % id)

    for entity_name in DELETABLE_ENTITIES:
        for entity in getattr(tag, entity_name):
            db.session.delete(entity)

    db.session.commit()

    entity_query = make_tags_query(id)

    schema = schemas.TagSchema()
    return schema.jsonify(entity_query.first()), 200
