#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2010-2019, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator management: REST API views
#
import flask

from snmpsim_control_plane.api import app
from snmpsim_control_plane.api import db
from snmpsim_control_plane.api.models import mgmt as models
from snmpsim_control_plane.api.schemas import mgmt as schemas

PREFIX = '/snmpsim/mgmt/v1'


@app.route(PREFIX + '/endpoints')
def show_endpoints():
    endpoints = (
        models.Endpoint
        .query
        .outerjoin(models.EngineEndpoint)
        .outerjoin(models.Engine)
        .all())

    schema = schemas.EndpointSchema(many=True)
    return schema.jsonify(endpoints)


@app.route(PREFIX + '/endpoints/<id>', methods=['GET'])
def show_endpoint(id):
    endpoint = (
        models.Endpoint
        .query
        .filter_by(id=id)
        .outerjoin(models.EngineEndpoint)
        .outerjoin(models.Engine)
        .first())

    schema = schemas.EndpointSchema(many=True)
    return schema.jsonify(endpoint)


@app.route(PREFIX + '/endpoints', methods=['POST'])
def new_endpoint():
    req = flask.request.json

    endpoint = models.Endpoint(**req)
    db.session.add(endpoint)
    db.session.commit()

    schema = schemas.EndpointSchema()
    return schema.jsonify(endpoint)


@app.route(PREFIX + '/endpoints/<id>', methods=['DELETE'])
def del_endpoint(id):
    endpoint = (
        models.Endpoint
        .query
        .filter_by(id=id)
        .first())

    db.session.delete(endpoint)
    db.session.commit()

    return flask.Response(status=201)


@app.route(PREFIX + '/users')
def show_users():
    schema = schemas.UserSchema(many=True)
    return schema.jsonify(models.User.query.all())


@app.route(PREFIX + '/users/<id>', methods=['GET'])
def show_user(id):
    user = (
        models.User
        .query
        .filter_by(id=id)
        .first())

    schema = schemas.UserSchema()
    return schema.jsonify(user)


@app.route(PREFIX + '/users', methods=['POST'])
def new_user():
    req = flask.request.json

    user = models.User(**req)
    db.session.add(user)
    db.session.commit()

    schema = schemas.UserSchema()
    return schema.jsonify(user)


@app.route(PREFIX + '/users/<id>', methods=['DELETE'])
def del_user(id):
    user = (
        models.User
        .query
        .filter_by(id=id)
        .first())

    db.session.delete(user)
    db.session.commit()

    return flask.Response(status=201)


@app.route(PREFIX + '/engines')
def show_engines():
    engines = (
        models.Engine
        .query
        .outerjoin(models.EngineUser)
        .outerjoin(models.User)
        .all())
    schema = schemas.EngineSchema(many=True)
    return schema.jsonify(engines)


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
        return flask.make_response('Not found', 404)

    schema = schemas.EngineSchema()
    return schema.jsonify(engine)


@app.route(PREFIX + '/engines', methods=['POST'])
def new_engine():
    req = flask.request.json

    engine = models.Engine(**req)
    db.session.add(engine)

    db.session.commit()

    schema = schemas.EngineSchema()
    return schema.jsonify(engine)


@app.route(PREFIX + '/engines/<id>', methods=['DELETE'])
def del_engine(id):
    engine = (
        models
        .Engine
        .query
        .filter_by(id=id)
        .first())

    db.session.delete(engine)
    db.session.commit()

    return flask.Response(status=201)


@app.route(PREFIX + '/engines/<id>/user/<user_id>', methods=['PUT'])
def add_engine_user(id, user_id):
    engine_user = models.EngineUser(user_id=user_id, engine_id=id)

    db.session.add(engine_user)
    db.session.commit()

    engine = models.Engine.query.filter_by(id=id).first()
    schema = schemas.EngineSchema()
    return schema.jsonify(engine)


@app.route(PREFIX + '/engines/<id>/user/<user_id>', methods=['DELETE'])
def del_engine_user(id, user_id):
    engine_user = (
        models
        .EngineUser
        .query
        .filter_by(engine_id=id, user_id=user_id)
        .first())

    db.session.delete(engine_user)
    db.session.commit()

    engine = models.Engine.query.filter_by(id=id).first()
    schema = schemas.EngineSchema()
    return schema.jsonify(engine)


@app.route(PREFIX + '/engines/<id>/endpoint/<endpoint_id>', methods=['PUT'])
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
    return schema.jsonify(engine)


@app.route(PREFIX + '/engines/<id>/endpoint/<endpoint_id>', methods=['DELETE'])
def del_engine_endpoint(id, endpoint_id):
    engine_endpoint = (
        models
        .EngineEndpoint
        .query
        .filter_by(engine_id=id, endpoint_id=endpoint_id).first())

    db.session.delete(engine_endpoint)
    db.session.commit()

    engine = models.Engine.query.filter_by(id=id).first()
    schema = schemas.EngineSchema()

    return schema.jsonify(engine)


@app.route(PREFIX + '/agents')
def show_agents():
    agents = (
        models.Agent
        .query
        .outerjoin(models.AgentEngine)
        .outerjoin(models.Engine)
        .all())

    schema = schemas.AgentSchema(many=True)
    return schema.jsonify(agents)


@app.route(PREFIX + '/agents/<id>', methods=['GET'])
def show_agent(id):
    agent = (
        models.Agent
        .query
        .filter_by(id=id)
        .outerjoin(models.AgentEngine)
        .outerjoin(models.Engine)
        .first())

    schema = schemas.AgentSchema()
    return schema.jsonify(agent)


@app.route(PREFIX + '/agents', methods=['POST'])
def new_agent():
    req = flask.request.json

    agent = models.Agent(**req)
    db.session.add(agent)
    db.session.commit()

    schema = schemas.AgentSchema()
    return schema.jsonify(agent)


@app.route(PREFIX + '/agents/<id>', methods=['DELETE'])
def del_agent(id):
    agent = (
        models
        .Agent
        .query
        .filter_by(id=id)
        .first())

    db.session.delete(agent)
    db.session.commit()

    return flask.Response(status=201)


@app.route(PREFIX + '/agents/<id>/engine/<engine_id>', methods=['PUT'])
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
    return schema.jsonify(agent)


@app.route(PREFIX + '/agents/<id>/engine/<engine_id>', methods=['DELETE'])
def del_agent_engine(id, engine_id):
    agent_engine = (
        models
        .AgentEngine
        .query
        .filter_by(engine_id=id, agent_id=agent_id).first())

    db.session.delete(agent_engine)
    db.session.commit()

    agent = (
        models
        .Agent
        .query
        .filter_by(id=id).first())

    schema = schemas.AgentSchema()
    return schema.jsonify(agent)


@app.route(PREFIX + '/selectors')
def show_selectors():
    selectors = (
        models.Selector
        .query
        .outerjoin(models.AgentSelector)
        .outerjoin(models.Agent)
        .all())

    schema = schemas.SelectorSchema(many=True)
    return schema.jsonify(selectors)


@app.route(PREFIX + '/selectors/<id>', methods=['GET'])
def show_selector(id):
    selector = (
        models.Selector
        .query
        .filter_by(id=id)
        .outerjoin(models.AgentSelector)
        .outerjoin(models.Agent)
        .first())

    schema = schemas.SelectorSchema()
    return schema.jsonify(selector)


@app.route(PREFIX + '/selectors', methods=['POST'])
def new_selector():
    req = flask.request.json

    selector = models.Selector(**req)
    db.session.add(selector)
    db.session.commit()

    schema = schemas.SelectorSchema()
    return schema.jsonify(selector)


@app.route(PREFIX + '/selectors/<id>', methods=['DELETE'])
def del_selector(id):
    selector = (
        models.Selector
        .query
        .filter_by(id=id)
        .first())

    db.session.delete(selector)
    db.session.commit()

    return flask.Response(status=201)


@app.route(PREFIX + '/agents/<id>/selector/<selector_id>/<order>', methods=['PUT'])
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
    return schema.jsonify(agent)


@app.route(PREFIX + '/agents/<id>/selector/<selector_id>', methods=['DELETE'])
def del_agent_selector(id, engine_id):
    agent_selector = (
        models
        .AgentSelector
        .query
        .filter_by(selector_id=id, agent_id=agent_id).first())

    db.session.delete(agent_selector)
    db.session.commit()

    agent = (
        models
        .Agent
        .query
        .filter_by(id=id).first())

    schema = schemas.AgentSchema()
    return schema.jsonify(agent)


@app.route(PREFIX + '/recordings')
def show_recordings():
    recordings = (
        models.Recording
        .query
        .all())

    schema = schemas.RecordingSchema(many=True)
    return schema.jsonify(recordings)


@app.route(PREFIX + '/recordings/<id>', methods=['GET'])
def show_recording(id):
    recording = (
        models.Recording
        .query
        .filter_by(id=id)
        .first())

    schema = schemas.RecordingSchema()
    return schema.jsonify(recording)


@app.route(PREFIX + '/recordings', methods=['POST'])
def new_recording():
    req = flask.request.json

    recording = models.Recording(**req)
    db.session.add(recording)
    db.session.commit()

    schema = schemas.RecordingSchema()
    return schema.jsonify(recording)


@app.route(PREFIX + '/recordings/<id>', methods=['DELETE'])
def del_recording(id):
    recording = (
        models.Recording
        .query
        .filter_by(id=id)
        .first())

    db.session.delete(recording)
    db.session.commit()

    return flask.Response(status=201)


@app.route(PREFIX + '/labs')
def show_labs():
    labs = (
        models.Lab
        .query
        .outerjoin(models.LabAgent)
        .outerjoin(models.Agent)
        .all())

    schema = schemas.LabSchema(many=True)
    return schema.jsonify(labs)


@app.route(PREFIX + '/labs/<id>', methods=['GET'])
def show_lab(id):
    lab = (
        models.Lab
        .query
        .filter_by(id=id)
        .outerjoin(models.LabAgent)
        .outerjoin(models.Agent)
        .first())

    schema = schemas.LabSchema()
    return schema.jsonify(lab)


@app.route(PREFIX + '/labs', methods=['POST'])
def new_lab():
    req = flask.request.json

    lab = models.Lab(**req)
    db.session.add(lab)
    db.session.commit()

    schema = schemas.LabSchema()
    return schema.jsonify(lab)


@app.route(PREFIX + '/labs/<id>', methods=['DELETE'])
def del_lab(id):
    lab = (
        models
        .Lab
        .query
        .filter_by(id=id)
        .first())

    db.session.delete(lab)
    db.session.commit()

    return flask.Response(status=201)


@app.route(PREFIX + '/labs/<id>/agent/<agent_id>', methods=['PUT'])
def add_lab_agent(id, agent_id):
    lab_agent = models.LabAgent(agent_id=agent_id, lab_id=id)

    db.session.add(lab_agent)
    db.session.commit()

    lab = models.Lab.query.filter_by(id=id).first()

    schema = schemas.LabSchema()
    return schema.jsonify(lab)


@app.route(PREFIX + '/labs/<id>/agent/<agent_id>', methods=['DELETE'])
def del_lab_agent(id, agent_id):
    lab_agent = (
        models
        .LabAgent
        .query
        .filter_by(agent_id=agent_id, lab_id=id)
        .first())

    db.session.delete(lab_agent)
    db.session.commit()

    engine = models.Engine.query.filter_by(id=id).first()
    schema = schemas.EngineSchema()
    return schema.jsonify(engine)


@app.route(PREFIX + '/labs/<id>/power', methods=['PUT'])
def change_lab_power(id, state):
    lab = (
        models.Lab
        .query
        .filter_by(id=id)
        .first())

    lab.power = state

    db.session.commit()

    lab = models.Lab.query.filter_by(id=id).first()

    schema = schemas.LabSchema()
    return schema.jsonify(lab)
