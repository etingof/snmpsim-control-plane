#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2010-2019, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator management: REST API document model
#
from snmpsim_control_plane.api import db


class Endpoint(db.Model):
    id = db.Column('id', db.Integer(), primary_key=True)
    name = db.Column('name', db.String(), nullable=True)
    domain = db.Column(
        'domain', db.String(64), unique=True, nullable=False)
    address = db.Column(
        'address', db.String(64), unique=True, nullable=False)
    engines = db.relationship(
        'EngineEndpoint', cascade="all,delete", backref='endpoint', lazy=True)


class User(db.Model):
    id = db.Column('id', db.Integer(), primary_key=True)
    user = db.Column('user', db.String(32), unique=True)
    name = db.Column(db.String(60))
    level = db.Column(db.String(12), nullable=False)
    auth_key = db.Column(db.String())
    auth_proto = db.Column(db.String(8), nullable=False)
    priv_key = db.Column(db.String())
    priv_proto = db.Column(db.String(8), nullable=False)
    engines = db.relationship(
        'EngineUser', cascade="all,delete", backref='user', lazy=True)


class Engine(db.Model):
    id = db.Column('id', db.Integer(), primary_key=True)
    engine_id = db.Column('engine_id', db.String(32), unique=True)
    users = db.relationship(
        'User', cascade="all,delete", secondary='engine_user',
        backref='engine', lazy=True)
    agents = db.relationship(
        'Agent', cascade="all,delete", secondary='agent_engine',
        backref='engine', lazy=True)
    endpoints = db.relationship(
        'Endpoint', cascade="all,delete", secondary='engine_endpoint',
        backref='engine', lazy=True)


class EngineUser(db.Model):
    engine_id = db.Column(
        db.Integer, db.ForeignKey("engine.id"), nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('engine_id', 'user_id'),
    )


class EngineEndpoint(db.Model):
    engine_id = db.Column(
        db.Integer, db.ForeignKey("engine.id"), nullable=False)
    endpoint_id = db.Column(
        db.Integer, db.ForeignKey("endpoint.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('engine_id', 'endpoint_id'),
    )


class Selector(db.Model):
    id = db.Column('id', db.Integer(), primary_key=True)
    comment = db.Column('comment', db.String())
    template = db.Column('template', db.String())
    agents = db.relationship(
        'Agent', cascade="all,delete", backref='selector', lazy=True)


class Agent(db.Model):
    id = db.Column('id', db.Integer(), primary_key=True)
    name = db.Column('name', db.String(), nullable=True)
    engine_id = db.Column(db.Integer, db.ForeignKey('engine.id'))
    selector_id = db.Column(db.Integer, db.ForeignKey('selector.id'))
    engines = db.relationship(
        'Engine', cascade="all,delete", secondary='agent_engine',
        backref='agent', lazy=True)
    selectors = db.relationship(
        'Selector', cascade="all,delete", secondary='agent_selector',
        backref='agent', lazy=True)
    labs = db.relationship(
        'Lab', cascade="all,delete", secondary='lab_agent',
        backref='agent', lazy=True)


class AgentEngine(db.Model):
    engine_id = db.Column(
        db.Integer, db.ForeignKey("engine.id"), nullable=False)
    agent_id = db.Column(
        db.Integer, db.ForeignKey("agent.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('engine_id', 'agent_id'),
    )


class AgentSelector(db.Model):
    order = db.Column('order', db.Integer())
    selector_id = db.Column(
        db.Integer, db.ForeignKey("selector.id"), nullable=False)
    agent_id = db.Column(
        db.Integer, db.ForeignKey("agent.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('selector_id', 'agent_id'),
    )


class Recording(db.Model):
    id = db.Column('id', db.Integer(), primary_key=True)
    name = db.Column(db.String(60))
    path = db.Column(db.String(), unique=True, nullable=False)


class Lab(db.Model):
    id = db.Column('id', db.Integer(), primary_key=True)
    name = db.Column('name', db.String(), nullable=True)
    power = db.Column('power', db.String(), nullable=True)
    agents = db.relationship(
        'Agent', cascade="all,delete", secondary='lab_agent',
        backref='lab', lazy=True)


class LabAgent(db.Model):
    lab_id = db.Column(
        db.Integer, db.ForeignKey("lab.id"), nullable=False)
    agent_id = db.Column(
        db.Integer, db.ForeignKey("agent.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('lab_id', 'agent_id'),
    )
