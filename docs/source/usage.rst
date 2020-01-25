
.. _usage:


Usage
-----

From user's perspective, SNMP Simulator Control Plane has two loosely coupled
APIs - Management and Metrics.

.. _simulator_management:

Simulator management
++++++++++++++++++++

To make sense of Management API, the user can follow
`Management <https://app.swaggerhub.com/apis/etingof/snmpsim-mgmt/1.0.0>`_
OpenAPI specification to build REST API queries assembling "virtual laboratories" of
SNMP agents.

The configurable components and their relationships is depicted on the
following diagram:

.. image:: components.png

Building a virtual laboratory involves creating one, then creating SNMP agent
(with all its dependent components) and linking it to transport endpoints, on
which the agent is listening for SNMP commands. Then linking this agent to
the lab.

Recordings do not have any rigid linkage. Instead the recording is picked
by the agent at run time based on SNMP message properties. The logic
of mapping is guided by the `selector` abstraction (not yet implemented).

For example, this is the Management REST API call for creating a virtual
laboratory:

.. code-block:: bash

    $ curl -d '{
          "name": "Test Lab"
        }' \
        -H 'Content-Type: application/json' \
        -X POST http://localhost:5000/snmpsim/mgmt/v1/labs

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

Here is a shortened though operational example of configuring a simple
virtual lab having one SNMP agent with one SNMPv3 user serving one
simulation data recording:

.. literalinclude:: ../../conf/bootstraps/minimal.sh
   :language: bash

Direct links to the above `script <./../conf/bootstraps/minimal.sh>`_ and
its supporting `library <./../conf/bootstraps/functions.sh>`_.

.. _gathering_metrics:

Gathering metrics
+++++++++++++++++

Metrics part of Control Plane provides ever growing counters reflecting
the operations of SNMP Simulator Command Responder instances running under
the supervision of `snmpsim-mgmt-supervisor` tool.

Besides that, `snmpsim-mgmt-supervisor` process collects OS-level metrics
on SNMP simulator instance processes.

The consumer of this service can follow
`Metrics <https://app.swaggerhub.com/apis/etingof/snmpsim-metrics/1.0.0>`_
OpenAPI specification to build queries requesting slices of data.

.. _agent_metrics:

SNMP agent metrics
~~~~~~~~~~~~~~~~~~

To get overall simulated SNMP agents activity:

.. code-block:: bash

    $ curl http://127.0.0.1:5001/snmpsim/metrics/v1/activity/messages
    {
      "_links": {
        "filters": "/snmpsim/metrics/v1/activity/messages/filters",
        "self": "/snmpsim/metrics/v1/activity/messages?"
      },
      "failures": 0,
      "pdus": 12497405,
      "var_binds": 14045935,
      "variations": [
        {
          "name": "numeric",
          "failures": 0,
          "total": 38644
        },
        {
          "name": "writecache",
          "failures": 0,
          "total": 13361
        }
      ]
    }

To discover available filtering criteria:

.. code-block:: bash

    $ curl http://127.0.0.1:5001/snmpsim/metrics/v1/activity/messages/filters
    {
      "context_engine_id": "/snmpsim/metrics/v1/activity/messages/filters/context_engine_id",
      "context_name": "/snmpsim/metrics/v1/activity/messages/filters/context_name",
      "engine_id": "/snmpsim/metrics/v1/activity/messages/filters/engine_id",
      "local_address": "/snmpsim/metrics/v1/activity/messages/filters/local_address",
      "pdu_type": "/snmpsim/metrics/v1/activity/messages/filters/pdu_type",
      "peer_address": "/snmpsim/metrics/v1/activity/messages/filters/peer_address",
      "protocol": "/snmpsim/metrics/v1/activity/messages/filters/protocol",
      "recording": "/snmpsim/metrics/v1/activity/messages/filters/recording",
      "security_level": "/snmpsim/metrics/v1/activity/messages/filters/security_level",
      "security_model": "/snmpsim/metrics/v1/activity/messages/filters/security_model"
    }

Zero or more of filtering criteria can then be added to the query string to compute
metrics for queries matching all given criteria at once:

All SNMPv3 queries so far:

.. code-block:: bash

    $ curl http://127.0.0.1:5001/snmpsim/metrics/v1/activity/messages?security_model=3
    {
      "_links": {
        "filters": "/snmpsim/metrics/v1/activity/messages/filters",
        "self": "/snmpsim/metrics/v1/activity/messages?security_model=3"
      },
      "failures": 0,
      "pdus": 1366419,
      "var_binds": 1672112,
      "variations": [
        {
          "name": "numeric",
          "failures": 0,
          "total": 4057
        },
        {
          "name": "writecache",
          "failures": 0,
          "total": 2364
        }
      ]
    }

How many SNMP commands have been received over UDP/IPv6 targeting SNMP communities
SNMPv3 context names *public* and *private*:

.. code-block:: bash

    $ curl http://127.0.0.1:5001/snmpsim/metrics/v1/activity/messages?protocol=udpv6\&recording=public.snmprec\&recording=private.snmprec
    {
      "_links": {
        "filters": "/snmpsim/metrics/v1/activity/messages/filters",
        "self": "/snmpsim/metrics/v1/activity/messages?protocol=udpv6&recording=public.snmprec"
      },
      "failures": 0,
      "pdus": 1423,
      "var_binds": 1692,
      "variations": []
    }

.. _process_metrics:

Process metrics
~~~~~~~~~~~~~~~

Process management metrics are taken at the OS-level, they have no ties with
SNMP whatsoever.

Supervisor tool metrics can be seen like this:

.. code-block:: bash

    $ curl http://127.0.0.1:5001/snmpsim/metrics/v1/supervisors
    [
      {
        "_links": {
          "collection": "/snmpsim/metrics/v1/supervisors",
          "self": "/snmpsim/metrics/v1/supervisors/1"
        },
        "hostname": "igarlic",
        "processes": [
          {
            "_links": {
              "self": "/snmpsim/metrics/v1/processes/1"
            },
            "path": "/opt/snmpsim/supervised/snmpsimd.sh"
          }
        ],
        "started": "2020-01-24T17:33:13+00:00",
        "watch_dir": "/opt/snmpsim/supervised"
        }
      }
    ]

To get specific SNMP simulator instance process metrics:

.. code-block:: bash

    $ curl http://127.0.0.1:5001/snmpsim/metrics/v1/processes/1
    {
      "_links": {
        "collection": "/snmpsim/metrics/v1/processes",
        "self": "/snmpsim/metrics/v1/processes/1"
      },
      "changes": 3,
      "console_pages": {
        "_links": {
          "self": "/snmpsim/metrics/v1/processes/1/console"
        },
        "count": 12,
        "last_update": "2020-01-24T17:36:13+00:00"
      },
      "cpu": 12,
      "endpoints": {
        "_links": {
          "self": "/snmpsim/metrics/v1/processes/1/endpoints"
        },
        "count": 4
      },
      "exits": 0,
      "files": 4,
      "id": 1,
      "last_update": "2020-01-24T17:36:14+00:00",
      "memory": 4178,
      "path": "/opt/snmpsim/supervised/snmpsimd.sh",
      "runtime": 60,
      "supervisor": {
        "_links": {
          "collection": "/snmpsim/metrics/v1/supervisors",
          "self": "/snmpsim/metrics/v1/supervisors/1"
        },
        "hostname": "igarlic",
        "watch_dir": "/opt/snmpsim/supervised"
      },
      "update_interval": 15
    }

Network interfaces and ports bound by SNMP simulator process can be
requested:

.. code-block:: bash

    $ curl http://127.0.0.1:5001/snmpsim/metrics/v1/processes/1/endpoints
    [
      {
        "_links": {
          "collection": "/snmpsim/metrics/v1/processes/1/endpoints",
          "self": "/snmpsim/metrics/v1/processes/1/endpoints/1"
        },
        "address": "::1:161",
        "process": {
          "_links": {
            "self": "/snmpsim/metrics/v1/processes/1"
          },
          "path": "/opt/snmpsim/supervised/snmpsimd.sh"
        },
        "protocol": "udpv6"
      },
      ...

Simulator process console output is collected and served:

.. code-block:: bash

    $ curl http://127.0.0.1:5001/snmpsim/metrics/v1/processes/1/console
    [
      {
        "_links": {
          "collection": "/snmpsim/metrics/v1/processes/1/console",
          "self": "/snmpsim/metrics/v1/processes/1/console/1"
        },
        "process": {
          "_links": {
            "self": "/snmpsim/metrics/v1/processes/1"
          },
          "path": "/opt/snmpsim/supervised/snmpsimd.sh"
        },
        "text": "Initializing variation modules...\n\
    --- SNMP Engine configuration\n\
    SNMPv3 EngineID: 0x80004fb805696761726c6963761cb1b8\n\
      --- Simulation data recordings configuration\n\
      SNMPv3 Context Engine ID: 0x80004fb805696761726c6963761cb1b8\n\
      Scanning "/opt/snmpsim/data" directory for  *.sapwalk, *.dump, *.MVC, *.snmprec, *.snm",\n",
        "timestamp": "2020-01-24T17:35:14+00:00"
      },
      ...

Metrics collection is a periodic, discreet process, by default metrics
traveling through the collection pipeline hit REST API DB every 15 seconds.
