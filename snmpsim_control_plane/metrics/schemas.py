#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator metrics: REST API view schemas
#
import marshmallow


class EnsureZeroMixIn(object):

    @marshmallow.pre_dump
    def ensure_zeros(self, item):
        return {key: getattr(item, key) or 0 for key in item.keys()}


class PacketsSchema(marshmallow.Schema, EnsureZeroMixIn):
    class Meta:
        fields = (
            'total', 'parse_failures',
            'auth_failures', 'context_failures')


class MessagesSchema(marshmallow.Schema, EnsureZeroMixIn):
    class Meta:
        fields = ('pdus', 'var_binds', 'failures', 'variations')

    variations = marshmallow.fields.Dict()


class VariationsSchema(marshmallow.Schema, EnsureZeroMixIn):
    class Meta:
        fields = ('name', 'total', 'failures')
