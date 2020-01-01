
Usage
-----

From user's perspective, SNMP Simulator Control Plane has two loosely coupled
APIs - Management and Metrics.

Simulator management
++++++++++++++++++++

To make sense of Management API, the user can follow
`Management <https://app.swaggerhub.com/apis/etingof/snmpsimd-control-plane/1.0.0>`_
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

Gathering metrics
+++++++++++++++++

Metrics part of Control Plane provides ever growing counters reflecting
the operations of SNMP Simulator Command Responder instances running under
the supervision of `snmpsim-mgmt-supervisor` tool.

The consumer of this service can follow
`Metrics <https://app.swaggerhub.com/apis/etingof/snmpsimd-monitoring/1.0.0>`_
OpenAPI specification to build queries requesting slices of data.

Examples
~~~~~~~~

To get overall SNMP simulator activity:

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
