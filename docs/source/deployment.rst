
Deployment
----------

This is a conceptual work flow of setting up Control Plane on your system.
The exact steps may differ.

Installation
++++++++++++

For production use, install SNMP Simulator and Control Plane tools
on your system:

.. code-block:: bash

   # Older setuptools may not work with versioned dependencies
   pip install setuptools -U

   pip install snmpsim-control-plane

   # Better use the latest (unreleased) SNMP Simulator
   pip install https://github.com/etingof/snmpsim/archive/master.zip

It's better to run all SNMP Simulator tools under a non-privileged user
and group (e.g. `snmpsim`).

.. code-block:: bash

    su snmpsim
    mkdir -p /var/snmpsim /etc/snmpsim /var/run/snmpsim /var/log/snmpsim

Configuration files
+++++++++++++++++++

Create configuration files for Management API tools:

.. code-block:: bash

    cat > /etc/snmpsim/snmpsim-management.conf <<EOF
    SQLALCHEMY_DATABASE_URI = 'sqlite:////var/snmpsim/snmpsim-mgmt-restapi.db'
    DEBUG = False
    SNMPSIM_MGMT_DATAROOT = '/var/snmpsim/data'
    SNMPSIM_MGMT_TEMPLATE = '/etc/snmpsim/snmpsim-command-responder.j2'
    SNMPSIM_MGMT_DESTINATION = '/var/snmpsim/supervised'
    EOF

And for Metrics API tools:

.. code-block:: bash

    cat > /etc/snmpsim/snmpsim-metrics.conf <<EOF
    SQLALCHEMY_DATABASE_URI = 'sqlite:////var/snmpsim/snmpsim-metrics-restapi.db'
    DEBUG = False
    EOF

Bootstrap underlying databases:

.. code-block:: bash

    snmpsim-mgmt-restapi --config /etc/snmpsim/snmpsim-management.conf \
        --recreate-db
    snmpsim-metrics-restapi --config /etc/snmpsim/snmpsim-metrics.conf \
        --recreate-db

SNMP Simulator options
++++++++++++++++++++++

To get SNMP Simulator Command Responder producing metrics we need to enable
that by passing the command-line option to the command responder process.
This can be done by modifying Management REST API template:

.. code-block:: bash

    cat > /etc/snmpsim/snmpsim-command-responder.j2 <<EOF
    {% if context['labs'] %}
    exec snmpsim-command-responder \
      --reporting-method fulljson:/tmp/snmpsim/reports \
      --proc-user snmpsim --proc-group snmpsim \
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

REST API servers
++++++++++++++++

To bring up REST API servers, just follow WSGI application setup guidelines.

For example, for `gunicorn <https://gunicorn.org>`_:

.. code-block:: bash

    pip install gunicorn

    gunicorn -b 127.0.0.1:5000 \
       --env "SNMPSIM_MGMT_CONFIG=/etc/snmpsim/snmpsim-management.conf" \
      --access-logfile /var/log/snmpsim/mgmt-access.log \
      --error-logfile /var/log/snmpsim/mgmt-error.log  \
      --daemon \
      snmpsim_control_plane.wsgi.management:app

    gunicorn -b 127.0.0.1:5001 \
      --env "SNMPSIM_METRICS_CONFIG=/etc/snmpsim/snmpsim-metrics.conf" \
      --access-logfile /var/log/snmpsim/metrics-access.log \
      --error-logfile /var/log/snmpsim/metrics-error.log  \
      --daemon \
      snmpsim_control_plane.wsgi.metrics:app

Work flow daemons
+++++++++++++++++

Then bring up the rest of the daemons:

.. code-block:: bash

   snmpsim-mgmt-supervisor \
     --config /etc/snmpsim/snmpsim-management.conf \
     --watch-dir /var/snmpsim/supervised \
     --daemonize \
     --pid-file /var/run/snmpsim/supervisor.pid \
     --logging-method file:/var/log/snmpsim/supervisor.log

   snmpsim-metrics-importer \
     --config /var/log/snmpsim/snmpsim-metrics.conf \
     --watch-dir /var/log/snmpsim/metrics \
     --daemonize \
     --pid-file /var/log/snmpsim/importer.pid \
     --logging-method file:/var/log/snmpsim/importer.log

Perhaps it's better to configure all process invocation commands within
systemd unit file or alike.

By this point you should be able to run REST API calls against Management
and Metrics REST API endpoints.

Calling REST APIs
+++++++++++++++++

To start using Control Plane, try uploading a simulation recording:

.. code-block:: bash

    cat > /tmp/public.snmprec <<EOF
    1.3.6.1.2.1.1.1.0|4|Linux zeus 4.8.6.5-smp #2 SMP Sun Nov 13 14:58:11 CDT 2016 i686
    1.3.6.1.2.1.1.2.0|6|1.3.6.1.4.1.8072.3.2.10
    1.3.6.1.2.1.1.3.0|67|123999999
    1.3.6.1.2.1.1.4.0|4|SNMP Laboratories, info@snmplabs.com
    1.3.6.1.2.1.1.5.0|4|zeus.snmplabs.com
    1.3.6.1.2.1.1.6.0|4|San Francisco, California, United States
    1.3.6.1.2.1.1.7.0|2|72
    1.3.6.1.2.1.1.8.0|67|123999999
    EOF

    curl -s -d "@/tmp/public.snmprec" \
      -H "Content-Type: text/plain" \
      -X POST \
      http://127.0.0.1:5000/snmpsim/mgmt/v1/recordings/public.snmprec

Followed by :doc:`configuring <usage>` and powering on a virtual laboratory.
