
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

How to use SNMP Simulator Control Plane
---------------------------------------

SNMP Simulator Control Plane tool (`snmpsim-restapi-mgmt`) is a typical Web
app. For experimenting and trying it out in a non-production environment,
it can be run stand-alone. For production use it's way better to run it
under a WSGI HTTP Server such as [gunicorn](https://gunicorn.org).

Once the `snmpsim-restapi-mgmt` tool is up and running, just follow OpenAPI
specification (shipped alone with this package) to configure your SNMP
Simulator instance by issuing a series of REST API calls.

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
remove one or more shell scripts that can be watched by the `snmpsim-supervisor`
tool to invoke SNMP simulator command responder instance(s) with desired
configuration.

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
      --data-dir "data" \

```

The above script is rendered from a Jinja2 template. If you need to have
SNMP simulator invoked somehow differently, just copy over the built-in
template, modify it and pass to the REST API server via a configuration
option.

Monitoring part of REST API provides ever growing counters reflecting the
operations of SNMP Simulator instances running under the supervision of
this control plane tool.

Download
--------

SNMP Simulator Control Plane tool is freely available for download from
[PyPI](https://pypi.org/project/snmpsim-control-plane/) or
[GitHub](https://github.com/etingof/snmpsim-control-plane/archive/master.zip).


Installation
------------

For production use, just `pip install snmpsim-control-plane` package
and follow general WSGI (Flask) application setup guidelines.

For development and testing, it is probably easier to set up everything
within a Python virtual environment:
 
```commandline
mkdir /tmp/snmpsim && cd /tmp/snmpsim

python3 -m venv venv

. venv/bin/activate

pip install https://github.com/etingof/snmpsim-control-plane/archive/master.zip
```

To make a real use of SNMP simulator control plane, consider installing
SNMP simulator into the same virtual environment as well:

```commandline
pip install https://github.com/etingof/snmpsim/archive/master.zip
```

Once everything is successfully installed, configure your control plane tools:

```commandline
mkdir -p /tmp/snmpsim/boot

cat > snmpsim-management.conf <<EOF
SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/snmpsim/snmpsim-restapi-management.db'
SQLALCHEMY_ECHO = False
SECRET_KEY = '\xfb\x12\xdf\xa1@i\xd6>V\xc0\xbb\x8fp\x16#Z\x0b\x81\xeb\x16'

DEBUG = True

SNMPSIM_MGMT_LISTEN_IP = '127.0.0.1'
SNMPSIM_MGMT_LISTEN_PORT = 8000

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
1.3.6.1.2.1.1.3.0|67:numeric|rate=100,initial=123999999
1.3.6.1.2.1.1.4.0|4|SNMP Laboratories, info@snmplabs.com
1.3.6.1.2.1.1.5.0|4:writecache|value=zeus.snmplabs.com (you can change this!)
1.3.6.1.2.1.1.6.0|4|San Francisco, California, United States
1.3.6.1.2.1.1.7.0|2|72
1.3.6.1.2.1.1.8.0|67:numeric|rate=100,initial=123999999
EOF
```

It might be easier to play with SNMP simulator control plane tools if
you have each running in the foreground:

```commandline
snmpsim-supervisor --watch-dir /tmp/snmpsim/boot
```

and (in a different shell, but same Python virtual environment):

```commandline
snmpsim-restapi-mgmt --config /tmp/snmpsim/snmpsim-management.conf \
    --recreate-db
snmpsim-restapi-mgmt --config /tmp/snmpsim/snmpsim-management.conf \
    --destination /tmp/snmpsim/boot
```

By this point you should be able to run REST API calls against control
plane and observe what happens. Look into
[conf/bootstraps/minimal.sh](https://github.com/etingof/snmpsim-control-plane/tree/master/conf/bootstraps)
for inspiration. Plain `curl` or highly automated
[Postman API client](https://www.getpostman.com/product/api-client) would work.

Getting help
------------

If something does not work as expected,
[open an issue](https://github.com/etingof/snmpsim-control-plane/issues) at GitHub or
post your question [on Stack Overflow](https://stackoverflow.com/questions/ask).

Feedback and collaboration
--------------------------

I'm interested in bug reports, fixes, suggestions and improvements. Your
pull requests are very welcome!

Copyright (c) 2019, [Ilya Etingof](mailto:etingof@gmail.com). All rights reserved.
