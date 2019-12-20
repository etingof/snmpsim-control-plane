
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

How to use SNMP Simulator Control Plane
---------------------------------------

SNMP Simulator Control Plane tool is a typical Web app. For experimenting and
trying it out in a non-production environment, it can be run stand-alone.
For production use it's way better to run it under a WSGI HTTP Server such
as [gunicorn](https://gunicorn.org).

Once the tool is up and running, just follow OpenAPI specification (shipped
alone with this package) to configure your SNMP Simulator instance by
issuing a series of REST API calls.

Monitoring part of REST API provides ever growing counters reflecting the
operations of SNMP Simulator instances running under the supervision of
this control plane tool.

Getting help
------------

If something does not work as expected,
[open an issue](https://github.com/etingof/snmpsim-control-plane/issues) at GitHub or
post your question [on Stack Overflow](https://stackoverflow.com/questions/ask).

Feedback and collaboration
--------------------------

I'm interested in bug reports, fixes, suggestions and improvements. Your
pull requests are very welcome!

Copyright (c) 2010-2019, [Ilya Etingof](mailto:etingof@gmail.com). All rights reserved.
