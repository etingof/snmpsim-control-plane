#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator metrics: REST API view schemas
#
import marshmallow
import flask

from snmpsim_control_plane.metrics import ma
from snmpsim_control_plane.metrics import models


class EnsureZeroMixIn(object):

    @marshmallow.pre_dump
    def ensure_zeros(self, item):
        return {key: getattr(item, key) or 0 for key in item.keys()}


class PacketsSchema(marshmallow.Schema, EnsureZeroMixIn):
    class Meta:
        fields = (
            'total', 'parse_failures', 'auth_failures',
            'context_failures')


class MessagesSchema(marshmallow.Schema, EnsureZeroMixIn):
    class Meta:
        fields = ('pdus', 'var_binds', 'failures', 'variations')

    variations = marshmallow.fields.Dict()


class VariationsSchema(marshmallow.Schema, EnsureZeroMixIn):
    class Meta:
        fields = ('name', 'total', 'failures')


class ConsoleSchema(ma.ModelSchema):
    class Meta:
        model = models.ConsolePage
        fields = ('id', 'timestamp', 'text', 'process', '_links')

    class ProcessSchema(ma.ModelSchema):
        class Meta:
            model = models.Process
            fields = ('id', 'path', '_links')

        _links = ma.Hyperlinks({
            'self': ma.URLFor('show_processes', id='<id>'),
        })

    process = ma.Nested(ProcessSchema)

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_console', id='<process_id>', page_id='<id>'),
        'collection': ma.URLFor('show_console', id='<process_id>')
    })


class EndpointSchema(ma.ModelSchema):
    class Meta:
        model = models.Endpoint
        fields = ('id', 'protocol', 'address', 'process', '_links')

    class ProcessSchema(ma.ModelSchema):
        class Meta:
            model = models.Process
            fields = ('id', 'path', '_links')

        _links = ma.Hyperlinks({
            'self': ma.URLFor('show_processes', id='<id>'),
        })

    process = ma.Nested(ProcessSchema)

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_endpoints', id='<process_id>', endpoint_id='<id>'),
        'collection': ma.URLFor('show_endpoints', id='<process_id>')
    })


class ProcessSchema(ma.ModelSchema):
    class Meta:
        model = models.Process
        fields = ('id', 'path', 'runtime', 'memory', 'cpu', 'files',
                  'exits', 'changes', 'last_update', 'update_interval',
                  'endpoints', 'supervisor', 'console_pages', '_links')

    class EndpointsSchema(ma.ModelSchema):
        class Meta:
            fields = ('count', '_links')

        count = marshmallow.fields.Method('get_count')
        _links = marshmallow.fields.Method('get_links')

        def get_count(self, endpoints):
            return len(endpoints)

        def get_links(self, endpoints):
            if endpoints:
                return {
                    'self': flask.url_for(
                        'show_endpoints', id=endpoints[0].process_id)
                }

            else:
                return {}

    endpoints = ma.Nested(EndpointsSchema)

    class ConsoleSchema(ma.ModelSchema):
        class Meta:
            model = models.ConsolePage
            fields = ('count', 'last_update', '_links')

        count = marshmallow.fields.Method('get_count')
        last_update = marshmallow.fields.Method('get_last_update')
        _links = marshmallow.fields.Method('get_links')

        def get_count(self, console_pages):
            return len(console_pages)

        def get_last_update(self, console_pages):
            if console_pages:
                return console_pages[-1].timestamp.isoformat() + '+00:00'

            return 0

        def get_links(self, console_pages):
            if console_pages:
                return {
                    'self': flask.url_for(
                        'show_console', id=console_pages[0].process_id)
                }

            else:
                return {}

    console_pages = ma.Nested(ConsoleSchema)

    class SupervisorSchema(ma.ModelSchema):
        class Meta:
            model = models.Supervisor
            fields = ('id', 'hostname', 'watch_dir', '_links')

        _links = ma.Hyperlinks({
            'self': ma.URLFor('show_supervisors', id='<id>'),
            'collection': ma.URLFor('show_supervisors')
        })

    supervisor = ma.Nested(SupervisorSchema)

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_processes', id='<id>'),
        'collection': ma.URLFor('show_processes')
    })


class SupervisorSchema(ma.ModelSchema):
    class Meta:
        model = models.Supervisor
        fields = ('id', 'hostname', 'watch_dir', 'started',
                  'processes', '_links')

    class ProcessSchema(ma.ModelSchema):
        class Meta:
            model = models.Process
            fields = ('id', 'path', '_links')

        _links = ma.Hyperlinks({
            'self': ma.URLFor('show_processes', id='<id>'),
        })

    processes = ma.Nested(ProcessSchema, many=True)

    _links = ma.Hyperlinks({
        'self': ma.URLFor('show_supervisors', id='<id>'),
        'collection': ma.URLFor('show_supervisors')
    })
