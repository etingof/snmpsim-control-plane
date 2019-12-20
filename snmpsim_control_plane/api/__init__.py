#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2010-2019, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator monitor: Flask application
#
import os

from flask import Flask
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy

import snmpsim_control_plane

CONFIG_FILE = os.path.join(
    os.path.dirname(snmpsim_control_plane.__file__),
    '..', 'conf', 'snmpsim-management.conf')

app = Flask(__name__)
app.config.from_pyfile(CONFIG_FILE)
db = SQLAlchemy(app)
ma = Marshmallow(app)

from snmpsim_control_plane.api.views import mgmt
