#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator management: REST API view schemas
#

from snmpsim_control_plane.management import ma
from snmpsim_control_plane.management import models


class EndpointSchema(ma.ModelSchema):
    class Meta:
        model = models.Endpoint
        fields = ('id', 'name', 'protocol', 'address', 'engines', '_links')

    engines = ma.Nested('EngineSchema', many=True, exclude=('endpoints',))

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_endpoint', id='<id>'),
        'collection': ma.URLFor('show_endpoints')
    })


class UserSchema(ma.ModelSchema):
    class Meta:
        model = models.User
        fields = ('id', 'user', 'name', 'auth_key',
                  'auth_proto', 'priv_key', 'priv_proto',
                  'engines', '_links')

    engines = ma.Nested('EngineSchema', many=True, exclude=('users',))

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_user', id='<id>'),
        'collection': ma.URLFor('show_users')
    })


class EngineSchema(ma.ModelSchema):
    class Meta:
        model = models.Engine
        fields = ('id', 'name', 'engine_id', 'users', 'endpoints',
                  'agents', '_links')

    users = ma.Nested(UserSchema, many=True, exclude=('engines',))
    endpoints = ma.Nested(EndpointSchema, many=True, exclude=('engines',))
    agents = ma.Nested('AgentSchema', many=True, exclude=('engines',))

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_engine', id='<id>'),
        'collection': ma.URLFor('show_engines')
    })


class SelectorSchema(ma.ModelSchema):
    class Meta:
        model = models.Selector
        fields = ('id', 'comment', 'template', 'agents', 'order', '_links')

    order = ma.Nested('AgentSelector')  # TODO: this does not work
    agents = ma.Nested('AgentSchema', many=True, exclude=('selectors',))

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_selector', id='<id>'),
        'collection': ma.URLFor('show_selectors')
    })


class AgentSchema(ma.ModelSchema):
    class Meta:
        model = models.Agent
        fields = ('id', 'name', 'engines', 'data_dir', 'selectors',
                  'labs', '_links')

    engines = ma.Nested(EngineSchema, many=True, exclude=('agents',))
    selectors = ma.Nested(SelectorSchema, many=True, exclude=('agents',))
    labs = ma.Nested('LabSchema', many=True, exclude=('agents',))

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_agent', id='<id>'),
        'collection': ma.URLFor('show_agents')
    })


class RecordingSchema(ma.ModelSchema):
    class Meta:
        fields = ('path', 'size', 'type')


class LabSchema(ma.ModelSchema):
    class Meta:
        model = models.Lab
        fields = ('id', 'name', 'power', 'agents', '_links')

    agents = ma.Nested(AgentSchema, many=True, exclude=('labs',))

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_lab', id='<id>'),
        'collection': ma.URLFor('show_labs')
    })
