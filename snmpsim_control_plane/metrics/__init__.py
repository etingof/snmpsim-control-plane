#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator monitor: Flask application
#
import os

from flask import Flask
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy

from snmpsim_control_plane.metrics import config


app = Flask(__name__)

app.url_map.strict_slashes = False

app.config.from_object(config.DefaultConfig)

if 'SNMPSIM_METRICS_CONFIG' in os.environ:
    app.config.from_envvar('SNMPSIM_METRICS_CONFIG')

db = SQLAlchemy(app)
ma = Marshmallow(app)
