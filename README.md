
SNMP Simulator Control Plane
----------------------------
[![PyPI](https://img.shields.io/pypi/v/snmpsim-control-plane.svg?maxAge=2592000)](https://pypi.org/project/snmpsim-control-plane/)
[![Python Versions](https://img.shields.io/pypi/pyversions/snmpsim-control-plane.svg)](https://pypi.org/project/snmpsim-control-plane/)
[![Build status](https://travis-ci.org/etingof/snmpsim-control-plane.svg?branch=master)](https://travis-ci.org/etingof/snmpsim-control-plane)
[![GitHub license](https://img.shields.io/badge/license-BSD-blue.svg)](https://raw.githubusercontent.com/etingof/snmpsim-control-plane/master/LICENSE.txt)

This package implements REST API driven management and monitoring supervisor to
remotely operate [SNMP simulator](http://snmplabs.com/snmpsim) instances.

Features
--------

* Makes SNMP Simulator remotely controllable
* Generates performance and operational metrics
* REST API is compliant to OpenAPI 3.0.0

SNMP Simulator Control Plane overview
-------------------------------------

SNMP Simulator Control Plane tools set includes a handful of daemons and
WSGI applications implementing REST API endpoints:

* `snmpsim-mgmt-restapi` - Management REST API server
* `snmpsim-mgmt-supervisor` - SNMP Simulator Command Responder instance
  supervisor
* `snmpsim-metrics-restapi` - System performance metrics reporting REST
  API server
* `snmpsim-metrics-importer` - Performance metrics DB importer

Once the system is up and running, the user can follow OpenAPI specification
(shipped alone with this package) to configure your SNMP Simulator instance
by issuing a series of REST API calls.

For example, to create a virtual laboratory:

```commandline
$ curl -d '{
      "name": "Test Lab"
    }' \
    -H 'Content-Type: application/json' \
    -X POST http://localhost:8000/snmpsim/mgmt/v1/labs

{
  "_links": {
    "collection": "/snmpsim/mgmt/v1/labs", 
    "self": "/snmpsim/mgmt/v1/labs/2"
  }, 
  "agents": [], 
  "id": 2, 
  "name": "Test Lab", 
  "power": "off"
}
```

Upon each configuration change, REST API server will create, update or
remove one or more shell scripts that can be watched by the
`snmpsim-mgmt-supervisor` tool to invoke SNMP simulator command responder
instance(s) with desired configuration.

For a minimal configuration with just one SNMP agent and one SNMPv3
USM user generated script will look like this:

```commandline
$ cat /tmp/snmpsim-run-labs.sh 
#!/bin/bash
#
# SNMP Simulator Command Responder invocation script
# Automatically generated from REST API DB data - do not edit!
#
exec snmpsim-command-responder \
    --v3-engine-id "auto" \
      --v3-user "simulator" \
      --agent-udpv4-endpoint "127.0.0.1:1161" \
      --data-dir "data"
```

The above script is rendered from a Jinja2 template. If you need to have
SNMP simulator invoked somehow differently, just copy over the built-in
template, modify it and pass to the REST API server via a configuration
option.

Metrics part of REST API provides ever growing counters reflecting the
operations of SNMP Simulator instances running under the supervision of
this control plane tool.

SNMP simulator command responder processes can be configured (via
`--reporting-method`) to collect and periodically dump various metrics.
One of the reporting methods is to write JSON files in certain format.

The `snmpsim-metrics-importer` daemon can collect these JSON files,
aggregate and load metrics into a SQL SB. Then `snmpsim-metrics-restapi`
server exposes collected metrics to REST API clients. For example,
this Metrics REST API call would reveal SNMP simulator activity:

```commandline
$ curl http://127.0.0.1:5001/snmpsim/metrics/v1/activity/messages
{
  "_links": {
    "filters": "/snmpsim/metrics/v1/activity/messages/filters", 
    "self": "/snmpsim/metrics/v1/activity/messages?"
  }, 
  "failures": 0, 
  "pdus": 25456, 
  "var_binds": 28392, 
  "variations": {
    "numeric": {
      "failures": 0, 
      "total": 66
    }, 
    "writecache": {
      "failures": 0, 
      "total": 26
    }
  }
}
```

Installation and configuration
------------------------------

For production use, just `pip install snmpsim-control-plane` package.
To bring up REST API servers, just follow WSGI application setup
guidelines.

For example, for [gunicorn](https://gunicorn.org):

```commandline
pip install gunicorn

gunicorn --env "SNMPSIM_MGMT_CONFIG=/etc/snmpsim/snmpsim-management.conf" \
  --access-logfile /var/log/snmpsim/mgmt-access.log \
  --error-logfile /var/log/snmpsim/mgmt-error.log  \
  --daemon \
  snmpsim_control_plane.wsgi.management:app

gunicorn --env "SNMPSIM_METRICS_CONFIG=/etc/snmpsim/snmpsim-metrics.conf" \
  --access-logfile /var/log/snmpsim/metrics-access.log \
  --error-logfile /var/log/snmpsim/metrics-error.log  \
  --daemon \
  snmpsim_control_plane.wsgi.metrics:app
```

For development and testing purposes, it is probably easier to set up
everything within a Python virtual environment:
 
```commandline
mkdir /tmp/snmpsim && cd /tmp/snmpsim

python3 -m venv venv

. venv/bin/activate

# older setuptools fail on versioned dependencies
pip install setuptools -U

pip install https://github.com/etingof/snmpsim-control-plane/archive/master.zip
```

To make a real use of SNMP simulator control plane, consider installing
SNMP simulator into the same virtual environment as well:

```commandline
pip install https://github.com/etingof/snmpsim/archive/master.zip
```

Once everything is successfully installed, configure your control plane tools.

Management API configuration
++++++++++++++++++++++++++++

Create REST API server configuration file:

```commandline
mkdir -p /tmp/snmpsim/boot

cat > snmpsim-management.conf <<EOF
SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/snmpsim/snmpsim-restapi-management.db'

DEBUG = True

SNMPSIM_MGMT_LISTEN_IP = '127.0.0.1'
SNMPSIM_MGMT_LISTEN_PORT = 5000

SNMPSIM_MGMT_SSL_CERT = None
SNMPSIM_MGMT_SSL_KEY = None
SNMPSIM_MGMT_DATAROOT = '/tmp/snmpsim/data'
SNMPSIM_MGMT_TEMPLATE = 'snmpsim-command-responder.j2'
SNMPSIM_MGMT_DESTINATION = '.'
EOF
```

You may want to put a simple SNMP simulation data file for SNMP simulator
to serve:

```commandline
mkdir -p /tmp/snmpsim/data

cat > /tmp/snmpsim/data/public.snmprec <<EOF
1.3.6.1.2.1.1.1.0|4|Linux zeus 4.8.6.5-smp #2 SMP Sun Nov 13 14:58:11 CDT 2016 i686
1.3.6.1.2.1.1.2.0|6|1.3.6.1.4.1.8072.3.2.10
1.3.6.1.2.1.1.3.0|67|123999999
1.3.6.1.2.1.1.4.0|4|SNMP Laboratories, info@snmplabs.com
1.3.6.1.2.1.1.5.0|4|zeus.snmplabs.com
1.3.6.1.2.1.1.6.0|4|San Francisco, California, United States
1.3.6.1.2.1.1.7.0|2|72
1.3.6.1.2.1.1.8.0|67|123999999
EOF
```

It might be easier to play with SNMP simulator control plane tools if
you have each running in the foreground:

```commandline
snmpsim-supervisor --watch-dir /tmp/snmpsim/boot
```

and (in a different shell, but same Python virtual environment):

```commandline
snmpsim-mgmt-restapi --config /tmp/snmpsim/snmpsim-management.conf \
    --recreate-db
snmpsim-mgmt-restapi --config /tmp/snmpsim/snmpsim-management.conf \
    --destination /tmp/snmpsim/boot
```

By this point you should be able to run REST API calls against management
control plane and observe what happens. Look into
[conf/bootstraps/minimal.sh](https://github.com/etingof/snmpsim-control-plane/tree/master/conf/bootstraps)
for inspiration. Plain `curl` or highly automated
[Postman API client](https://www.getpostman.com/product/api-client) would work.

Metrics API configuration
+++++++++++++++++++++++++

Create REST API server configuration file:

```commandline
cat > snmpsim-metrics.conf <<EOF
SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/snmpsim/snmpsim-restapi-metrics.db'

DEBUG = True

SNMPSIM_METRICS_LISTEN_IP = '127.0.0.1'
SNMPSIM_METRICS_LISTEN_PORT = 5001

EOF
```

To get SNMP simulator command responder producing metrics we need to enable that
by passing the command-line option to the command responder process. This can
be done by modifying Management REST API template:

```commandline
mkdir -p /tmp/snmpsim/reports

cat > /tmp/snmpsim/snmpsim-command-responder.j2 <<EOF
{% if context['labs'] %}
exec snmpsim-command-responder \
  --reporting-method fulljson:/tmp/snmpsim/reports \
  {% for lab in context['labs'] %}
    {% for agent in lab['agents'] %}
      {% for engine in agent['engines'] %}
    --v3-engine-id "{{ engine['engine_id'] }}" \
        {% for user in engine['users'] %}
      --v3-user "{{ user['user'] }}" \
          {% if user['auth_key'] is not none %}
      --v3-auth-key "{{ user['auth_key'] }}" \
      --v3-auth-proto "{{ user['auth_proto'] }}" \
            {% if user['priv_key'] is not none %}
      --v3-priv-key "{{ user['priv_key'] }}" \
      --v3-priv-proto "{{ user['priv_proto'] }}" \
            {% endif %}
          {% endif %}
        {% endfor %}
        {% for endpoint in engine['endpoints'] %}
      --agent-{{ endpoint['protocol'] }}-endpoint "{{ endpoint['address'] }}" \
        {% endfor %}
      --data-dir "{{ agent['data_dir'] }}" \
      {% endfor %}
    {% endfor %}
  {% endfor %}
{% endif %}
EOF
```

Re/start management REST API server with new template:

```commandline
snmpsim-mgmt-restapi --config /tmp/snmpsim/snmpsim-management.conf \
    --destination /tmp/snmpsim/boot \
    --template /tmp/snmpsim/snmpsim-command-responder.j2
```

Start metrics importing process over the same directory where SNMP
simulator command responder will push its reports to:

```commandline
snmpsim-metrics-importer --config /tmp/snmpsim/snmpsim-metrics.conf \
    --recreate-db
snmpsim-metrics-importer --config /tmp/snmpsim/snmpsim-metrics.conf \
    --watch-dir /tmp/snmpsim/reports
```

Start Metrics REST API server:

```commandline
snmpsim-restapi-metrics --config /tmp/snmpsim/snmpsim-metrics.conf
```

By this point you should be able to run REST API calls against metrics
endpoints.

Download
--------

SNMP Simulator Control Plane tool is freely available for download from
[PyPI](https://pypi.org/project/snmpsim-control-plane/) or
[GitHub](https://github.com/etingof/snmpsim-control-plane/archive/master.zip).

Getting help
------------

If something does not work as expected,
[open an issue](https://github.com/etingof/snmpsim-control-plane/issues) at GitHub or
post your question [on Stack Overflow](https://stackoverflow.com/questions/ask).

Feedback and collaboration
--------------------------

Bug reports, fixes, suggestions and improvements are welcome!

Copyright (c) 2019, [Ilya Etingof](mailto:etingof@gmail.com). All rights reserved.
