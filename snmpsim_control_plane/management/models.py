#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator management: REST API document model
#
import re

from sqlalchemy.orm import validates

from snmpsim_control_plane.management import db


class Endpoint(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=True)
    protocol = db.Column(db.Enum('udpv4', 'udpv6'), nullable=False)
    address = db.Column(db.String(64), unique=True, nullable=False)
    engines = db.relationship(
        'Engine', cascade="all,delete", secondary='engine_endpoint',
        backref='endpoint', lazy=True)

    @validates('address')
    def validate_address(self, key, address):
        # TODO: also match `protocol`
        ipv4 = re.match(r'[0-9]+(?:\.[0-9]+){3}(:[0-9]+)?$', address)
        if ipv4:
            return address

        ipv6 = re.match(r'\[([a-f0-9:]+:+)+[a-f0-9]+\](:[0-9]+)?$', address)
        if ipv6:
            return address

        raise Exception('Malformed IP address %s' % address)


class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user = db.Column(db.String(32), unique=True)
    name = db.Column(db.String(60))
    auth_key = db.Column(db.String(), nullable=True)
    auth_proto = db.Column(
        db.Enum("md5", "sha", "sha224", "sha256", "sha384", "sha512",
                "none"), default='none')
    priv_key = db.Column(db.String(), nullable=True)
    priv_proto = db.Column(
        db.Enum("des", "3des", "aes", "aes128", "aes192", "aes192blmt",
                "aes256", "aes256blmt", "none"), default='none')
    engines = db.relationship(
        'Engine', cascade="all,delete", secondary='engine_user',
        backref='user', lazy=True)


class Engine(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64), nullable=True)
    engine_id = db.Column(db.String(32), default='auto')
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
    id = db.Column(db.Integer(), primary_key=True)
    comment = db.Column(db.String())
    template = db.Column(db.String())
    agents = db.relationship(
        'Agent', cascade="all,delete", backref='selector', lazy=True)


class Agent(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=True)
    data_dir = db.Column(db.String(), default='.')
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
    order = db.Column(db.Integer())
    selector_id = db.Column(
        db.Integer, db.ForeignKey("selector.id"), nullable=False)
    agent_id = db.Column(
        db.Integer, db.ForeignKey("agent.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('selector_id', 'agent_id'),
    )


class Lab(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=True)
    power = db.Column(db.Enum('on', 'off'), default='off')
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
