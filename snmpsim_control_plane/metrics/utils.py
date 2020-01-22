#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator metrics: snmpsim metrics helpers
#
from sqlalchemy import func

from snmpsim_control_plane.metrics import db


def autoincrement(obj, model):
    """Add unique ID to model.

    Sqlalchemy's merge requires unique fields being primary keys. On top of
    that, autoincrement does not always work with Sqlalchemy. Thus this
    hack to generate unique row ID. %-(
    """
    if obj.id is None:
        max_id = db.session.query(func.max(model.id)).first()
        max_id = max_id[0]
        max_id = max_id + 1 if max_id else 1
        obj.id = max_id

        db.session.commit()

