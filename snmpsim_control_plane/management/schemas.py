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


class MinimalTagSchema(ma.ModelSchema):
    class Meta:
        model = models.Tag
        fields = ('id', 'name', 'description', '_links')

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_tag', id='<id>'),
        'collection': ma.URLFor('show_tags')
    })


class EndpointSchema(ma.ModelSchema):
    class Meta:
        model = models.Endpoint
        fields = ('id', 'name', 'protocol', 'address', 'engines',
                  'tags', '_links')

    engines = ma.Nested('EngineSchema', many=True, exclude=('endpoints',))
    tags = ma.Nested('MinimalTagSchema', many=True)

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_endpoint', id='<id>'),
        'collection': ma.URLFor('show_endpoints')
    })


class UserSchema(ma.ModelSchema):
    class Meta:
        model = models.User
        fields = ('id', 'user', 'name', 'auth_key',
                  'auth_proto', 'priv_key', 'priv_proto',
                  'engines', 'tags', '_links')

    engines = ma.Nested('EngineSchema', many=True, exclude=('users',))
    tags = ma.Nested('MinimalTagSchema', many=True)

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_user', id='<id>'),
        'collection': ma.URLFor('show_users')
    })


class EngineSchema(ma.ModelSchema):
    class Meta:
        model = models.Engine
        fields = ('id', 'name', 'engine_id', 'users', 'endpoints',
                  'agents', 'tags', '_links')

    users = ma.Nested(UserSchema, many=True, exclude=('engines',))
    endpoints = ma.Nested(EndpointSchema, many=True, exclude=('engines',))
    agents = ma.Nested('AgentSchema', many=True, exclude=('engines',))
    tags = ma.Nested('MinimalTagSchema', many=True)

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_engine', id='<id>'),
        'collection': ma.URLFor('show_engines')
    })


class SelectorSchema(ma.ModelSchema):
    class Meta:
        model = models.Selector
        fields = ('id', 'comment', 'template', 'agents', 'order',
                  'tags', '_links')

    order = ma.Nested('AgentSelector')  # TODO: this does not work
    agents = ma.Nested('AgentSchema', many=True, exclude=('selectors',))
    tags = ma.Nested('MinimalTagSchema', many=True)

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_selector', id='<id>'),
        'collection': ma.URLFor('show_selectors')
    })


class AgentSchema(ma.ModelSchema):
    class Meta:
        model = models.Agent
        fields = ('id', 'name', 'engines', 'data_dir', 'selectors',
                  'labs', 'tags', '_links')

    engines = ma.Nested(EngineSchema, many=True, exclude=('agents',))
    selectors = ma.Nested(SelectorSchema, many=True, exclude=('agents',))
    labs = ma.Nested('LabSchema', many=True, exclude=('agents',))
    tags = ma.Nested('MinimalTagSchema', many=True)

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
        fields = ('id', 'name', 'power', 'agents',
                  'tags', '_links')

    agents = ma.Nested(AgentSchema, many=True, exclude=('labs',))
    tags = ma.Nested('MinimalTagSchema', many=True)

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_lab', id='<id>'),
        'collection': ma.URLFor('show_labs')
    })


class TagSchema(MinimalTagSchema):
    class Meta:
        model = models.Tag
        fields = ('id', 'name', 'description', 'endpoints', 'users',
                  'engines', 'selectors', 'agents', 'labs', '_links')

    class EndpointSchema(EndpointSchema):
        class Meta:
            model = models.Endpoint
            fields = ('id', 'name', 'protocol', 'address', '_links')

    class UserSchema(UserSchema):
        class Meta:
            model = models.User
            fields = ('id', 'user', 'name', 'auth_key',
                      'auth_proto', 'priv_key', 'priv_proto',
                      '_links')

    class EngineSchema(EngineSchema):
        class Meta:
            model = models.Engine
            fields = ('id', 'name', 'engine_id', '_links')

    class SelectorSchema(SelectorSchema):
        class Meta:
            model = models.Selector
            fields = ('id', 'comment', 'template', 'order', '_links')

    class AgentSchema(AgentSchema):
        class Meta:
            model = models.Agent
            fields = ('id', 'name', 'data_dir', '_links')

    class LabSchema(LabSchema):
        class Meta:
            model = models.Lab
            fields = ('id', 'name', 'power', '_links')

    endpoints = ma.Nested(EndpointSchema, many=True, exclude=('tags',))
    users = ma.Nested(UserSchema, many=True, exclude=('tags',))
    engines = ma.Nested(EngineSchema, many=True, exclude=('tags',))
    selectors = ma.Nested(SelectorSchema, many=True, exclude=('tags',))
    agents = ma.Nested(AgentSchema, many=True, exclude=('tags',))
    labs = ma.Nested(LabSchema, many=True, exclude=('tags',))
