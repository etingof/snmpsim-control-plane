#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator management: turn ORM data into a tree of dicts
#
from sqlalchemy import and_
from sqlalchemy import inspect

from snmpsim_control_plane.management import models


def object_as_dict(obj):
    return {
        c.key: getattr(obj, c.key)
        for c in inspect(obj).mapper.column_attrs
    }


def to_dict():
    labs = []

    query = (
        models.Lab
        .query
        .filter_by(power='on')
    )

    for orm_lab in query:
        agents = []

        lab = object_as_dict(orm_lab)
        lab.update(agents=agents)
        labs.append(lab)

        for orm_agent in orm_lab.agents:
            engines = []
            selectors = []

            agent = object_as_dict(orm_agent)
            agent.update(engines=engines, selectors=selectors)
            agents.append(agent)

            for orm_engine in orm_agent.engines:
                users = []
                endpoints = []

                engine = object_as_dict(orm_engine)
                engine.update(users=users, endpoints=endpoints)
                engines.append(engine)

                for orm_user in orm_engine.users:
                    user = object_as_dict(orm_user)
                    users.append(user)

                for orm_endpoint in orm_engine.endpoints:
                    endpoint = object_as_dict(orm_endpoint)
                    endpoints.append(endpoint)

            for orm_selector in orm_agent.selectors:
                selector = object_as_dict(orm_selector)
                selectors.append(selector)

    context = {}

    if labs:
        context.update(labs=labs)

    return context
