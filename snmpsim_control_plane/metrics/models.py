#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator metrics: ORM models
#
from snmpsim_control_plane.metrics import db


class Transport(db.Model):
    id = db.Column(db.Integer(), unique=True)
    transport_protocol = db.Column(db.String(8), nullable=False)
    endpoint = db.Column(db.String(64), nullable=False)
    peer = db.Column(db.String(64), nullable=False)

    packets = db.relationship(
        'Packet', cascade="all,delete", backref='transports', lazy=True)

    # Sqlalchemy's merge requires unique fields to be primary keys
    __table_args__ = (
        db.PrimaryKeyConstraint(
            'transport_protocol', 'endpoint', 'peer'
        ),
    )


class Packet(db.Model):
    total = db.Column(db.BigInteger)
    parse_failures = db.Column(db.BigInteger)
    auth_failures = db.Column(db.BigInteger)
    context_failures = db.Column(db.BigInteger)

    transport_id = db.Column(
        db.Integer, db.ForeignKey("transport.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint(
            'transport_id'
        ),
    )


class Agent(db.Model):
    id = db.Column(db.Integer(), unique=True)
    transport_id = db.Column(
        db.Integer, db.ForeignKey("transport.id"), nullable=False)
    engine = db.Column(db.String(64), nullable=False)
    security_model = db.Column(db.Integer(), nullable=False)
    security_level = db.Column(db.Integer(), nullable=False)
    context_engine = db.Column(db.String(64), nullable=False)
    context_name = db.Column(db.String(64), nullable=False)

    recordings = db.relationship(
        'Recording', cascade="all,delete", backref='agent', lazy=True)

    # Sqlalchemy's merge requires unique fields to be primary keys
    __table_args__ = (
        db.PrimaryKeyConstraint(
            'transport_id', 'engine', 'security_model', 'security_level',
            'context_engine', 'context_name'
        ),
    )


class Recording(db.Model):
    id = db.Column(db.Integer(), unique=True)
    path = db.Column(db.String(16), nullable=False)

    agent_id = db.Column(
        db.Integer, db.ForeignKey("agent.id"), nullable=False)

    pdus = db.relationship(
        'Pdu', cascade="all,delete", backref='recording', lazy=True)

    __table_args__ = (
        db.PrimaryKeyConstraint(
            'agent_id', 'path'
        ),
    )


class Pdu(db.Model):
    id = db.Column(db.Integer(), unique=True)
    name = db.Column(db.String(16), nullable=False)
    total = db.Column(db.BigInteger)

    recording_id = db.Column(
        db.Integer, db.ForeignKey("recording.id"), nullable=False)

    varbinds = db.relationship(
        'VarBind', cascade="all,delete", backref='pdu', lazy=True)
    variations = db.relationship(
        'Variation', cascade="all,delete", backref='pdu', lazy=True)

    __table_args__ = (
        db.PrimaryKeyConstraint(
            'recording_id', 'name'
        ),
    )


class VarBind(db.Model):
    total = db.Column(db.BigInteger)
    failures = db.Column(db.BigInteger)
    pdu_id = db.Column(
        db.Integer, db.ForeignKey("pdu.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint(
            'pdu_id'
        ),
    )


class Variation(db.Model):
    name = db.Column(db.String(64), nullable=False)
    total = db.Column(db.BigInteger)
    failures = db.Column(db.BigInteger)
    pdu_id = db.Column(
        db.Integer, db.ForeignKey("pdu.id"), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint(
            'pdu_id', 'name'
        ),
    )
