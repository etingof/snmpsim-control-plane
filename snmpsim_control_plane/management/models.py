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


class Tag(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    description = db.Column(db.String(), nullable=True)

    endpoints = db.relationship(
        'Endpoint', secondary='tag_endpoint', back_populates='tags', lazy=True)
    users = db.relationship(
        'User', secondary='tag_user', back_populates='tags', lazy=True)
    engines = db.relationship(
        'Engine', secondary='tag_engine', back_populates='tags', lazy=True)
    selectors = db.relationship(
        'Selector', secondary='tag_selector', back_populates='tags', lazy=True)
    agents = db.relationship(
        'Agent', secondary='tag_agent', back_populates='tags', lazy=True)
    labs = db.relationship(
        'Lab', secondary='tag_lab', back_populates='tags', lazy=True)


class Endpoint(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=True)
    protocol = db.Column(db.Enum('udpv4', 'udpv6'), nullable=False)
    address = db.Column(db.String(64), unique=True, nullable=False)
    engines = db.relationship(
        'Engine', secondary='engine_endpoint',
        back_populates='endpoints', lazy=True)
    tags = db.relationship(
        'Tag', secondary='tag_endpoint', back_populates='endpoints', lazy=True)

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


class TagEndpoint(db.Model):
    tag_id = db.Column(
        db.Integer, db.ForeignKey("tag.id"), nullable=False)
    endpoint_id = db.Column(
        db.Integer, db.ForeignKey("endpoint.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('tag_id', 'endpoint_id'),
    )


class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user = db.Column(db.String(32), unique=True)
    name = db.Column(db.String(60))
    auth_key = db.Column(db.String(), nullable=True)
    auth_proto = db.Column(
        db.Enum("MD5", "SHA", "SHA224", "SHA256", "SHA384", "SHA512",
                "NONE"), default='NONE')
    priv_key = db.Column(db.String(), nullable=True)
    priv_proto = db.Column(
        db.Enum("DES", "3DES", "AES", "AES128", "AES192", "AES192BLMT",
                "AES256", "AES256BLMT", "NONE"), default='NONE')
    engines = db.relationship(
        'Engine', secondary='engine_user', back_populates='users', lazy=True)
    tags = db.relationship(
        'Tag', secondary='tag_user', back_populates='users', lazy=True)

    @validates('auth_proto')
    def uppercase_auth_proto(self, key, proto):
        return proto.upper()

    @validates('priv_proto')
    def uppercase_priv_proto(self, key, proto):
        return proto.upper()

    __table_args__ = (
        db.CheckConstraint(
            "auth_key IS NULL AND auth_proto='NONE' OR "
            "auth_key IS NOT NULL AND length(auth_key) > 7 "
            "AND auth_proto!='NONE'",
            name='auth_key_check'),
        db.CheckConstraint(
            "priv_key IS NULL AND priv_proto='NONE' OR "
            "priv_key IS NOT NULL AND length(priv_key) > 7 "
            "AND priv_proto!='NONE'",
            name='priv_key_check'),
        db.CheckConstraint(
            "priv_proto='NONE' OR "
            "priv_proto!='NONE' AND auth_proto!='NONE'",
            name='auth_priv_check'),
    )


class TagUser(db.Model):
    tag_id = db.Column(
        db.Integer, db.ForeignKey("tag.id"), nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('tag_id', 'user_id'),
    )


class Engine(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(64), nullable=True)
    engine_id = db.Column(db.String(32), default='auto')
    users = db.relationship(
        'User', secondary='engine_user',
        back_populates='engines', lazy=True)
    agents = db.relationship(
        'Agent', secondary='agent_engine',
        back_populates='engines', lazy=True)
    endpoints = db.relationship(
        'Endpoint', secondary='engine_endpoint',
        back_populates='engines', lazy=True)
    tags = db.relationship(
        'Tag', secondary='tag_engine', back_populates='engines', lazy=True)


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


class TagEngine(db.Model):
    tag_id = db.Column(
        db.Integer, db.ForeignKey("tag.id"), nullable=False)
    engine_id = db.Column(
        db.Integer, db.ForeignKey("engine.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('tag_id', 'engine_id'),
    )


class Selector(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    comment = db.Column(db.String())
    template = db.Column(db.String())
    agents = db.relationship(
        'Agent', backref='selector', lazy=True)
    tags = db.relationship(
        'Tag', secondary='tag_selector', back_populates='selectors', lazy=True)


class TagSelector(db.Model):
    tag_id = db.Column(
        db.Integer, db.ForeignKey("tag.id"), nullable=False)
    selector_id = db.Column(
        db.Integer, db.ForeignKey("selector.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('tag_id', 'selector_id'),
    )


class Agent(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=True)
    data_dir = db.Column(db.String(), default='.')
    engine_id = db.Column(db.Integer, db.ForeignKey('engine.id'))
    selector_id = db.Column(db.Integer, db.ForeignKey('selector.id'))
    engines = db.relationship(
        'Engine', secondary='agent_engine', back_populates='agents', lazy=True)
    selectors = db.relationship(
        'Selector', secondary='agent_selector', back_populates='agents', lazy=True)
    labs = db.relationship(
        'Lab', secondary='lab_agent', back_populates='agents', lazy=True)
    tags = db.relationship(
        'Tag', secondary='tag_agent', back_populates='agents', lazy=True)


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


class TagAgent(db.Model):
    tag_id = db.Column(
        db.Integer, db.ForeignKey("tag.id"), nullable=False)
    agent_id = db.Column(
        db.Integer, db.ForeignKey("agent.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('tag_id', 'agent_id'),
    )


class Lab(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=True)
    power = db.Column(db.Enum('on', 'off'), default='off')
    agents = db.relationship(
        'Agent', secondary='lab_agent', back_populates='labs', lazy=True)
    tags = db.relationship(
        'Tag', secondary='tag_lab', back_populates='labs', lazy=True)


class LabAgent(db.Model):
    lab_id = db.Column(
        db.Integer, db.ForeignKey("lab.id"), nullable=False)
    agent_id = db.Column(
        db.Integer, db.ForeignKey("agent.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('lab_id', 'agent_id'),
    )


class TagLab(db.Model):
    tag_id = db.Column(
        db.Integer, db.ForeignKey("tag.id"), nullable=False)
    lab_id = db.Column(
        db.Integer, db.ForeignKey("lab.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('tag_id', 'lab_id'),
    )
