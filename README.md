
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

Once the tool is up and running, just follow OpenAPI specification (shipped
alone with this package) to configure your SNMP Simulator instance by
issuing a series of REST API calls.

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

Complete SNMP simulator bootstrapping sequences can be found in the
`conf/bootstraps` directory.

Upon each configuration change, REST API server will re-create one or
more shell scripts that can be used to invoke SNMP simulator command
responder having desired configuration.

For a minimal configuration with just one SNMP agent and one SNMPv3
USM user generated script will look like this:

```commandline
$ cat /tmp/snmpsim-run-labs.sh 
#!/bin/bash
#
# SNMP Simulator Command Responder invocation script
# Automatically generated from REST API DB data - do not edit!
#
snmpsim-command-responder \
    --logging-method file:/var/log/snmpsim/snmpsim-command-responder.log:1D \
    --cache-dir /tmp/snmpsim/cache \
    --process-user snmpsim --process-group snmpsim \
    --v3-engine-id "auto" \
      --v3-user "simulator" \
      --agent-udpv4-endpoint "127.0.0.1:1161" \
      --data-dir "data" \

```

Monitoring part of REST API provides ever growing counters reflecting the
operations of SNMP Simulator instances running under the supervision of
this control plane tool.

Download
--------

SNMP Simulator Control Plane tool is freely available for download from
[PyPI](https://pypi.org/project/snmpsim-control-plane/).

Installation
------------

Just run:

```bash
$ pip install snmpsim-control-plane
```

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
