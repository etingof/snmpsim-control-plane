#!/bin/bash
#
# Stand up SNMP simulator command responder metrics REST API
# along with metrics collector. Feed the latter a sample metrics
# report and issue a series of REST API calls to make sure metrics
# showed up in REST API endpoints.
#
# Fail the entire script on any failure.
#
ENDPOINT=http://localhost:5001/snmpsim/metrics/v1

set -e

function get_field() {
    endpoint=$1
    field=$2

    curl -s \
          $endpoint | \
        python -c "
import sys, json

rsp = {}

try:
    rsp = json.load(sys.stdin)

    sys.stdout.write('%s' % rsp['$field'])

except Exception as exc:
    sys.stderr.write('API error #%s (%s)\n' % (rsp.get('status', '?'), rsp.get('message', exc)))
    sys.exit(1)
"

    if [ $? -ne 0 ]; then
      return 1
    fi
}


RESTAPI_CONF=$(mktemp /tmp/snmpsim-metrics.XXXXXX)

sed -e 's/DEBUG = True/DEBUG = False/g' $(pwd)/conf/snmpsim-metrics.conf > $RESTAPI_CONF

snmpsim-metrics-restapi \
    --config $RESTAPI_CONF \
    --recreate-db

RESTAPI_WATCH_DIR=$(mktemp -d /tmp/snmpsim-metrics.XXXXXX)

snmpsim-metrics-restapi \
    --config $RESTAPI_CONF &

RESTAPI_PID=$!

snmpsim-metrics-importer \
    --config $RESTAPI_CONF \
    --watch-dir $RESTAPI_WATCH_DIR &

IMPORTER_PID=$!

function cleanup()
{
    rm -fr "$RESTAPI_WATCH_DIR" $RESTAPI_CONF
    kill $IMPORTER_PID $RESTAPI_PID && true
}

trap cleanup EXIT

sleep 10

cp $(pwd)/tests/integration/samples/*.json $RESTAPI_WATCH_DIR

sleep 10

if compgen -G "$RESTAPI_WATCH_DIR/*"; then
    echo "Metrics not consumed"
    exit 1
fi

total=$(get_field "$ENDPOINT/activity/packets" "total")

if [ $total -ne 12728 ]; then
    echo "Wrong total packet count $total"
    exit 1
fi

pdus=$(get_field "$ENDPOINT/activity/messages" "pdus")

if [ $pdus -ne 12728 ]; then
    echo "Wrong total pdus count $pdus"
    exit 1
fi

var_binds=$(get_field "$ENDPOINT/activity/messages" "var_binds")

if [ $var_binds -ne 14196 ]; then
    echo "Wrong total var_binds count $var_binds"
    exit 1
fi

failures=$(get_field "$ENDPOINT/activity/messages" "failures")

if [ $failures -ne 0 ]; then
    echo "Wrong total failures count $failures"
    exit 1
fi

hostname=$(get_field "$ENDPOINT/supervisors/1" "hostname")

if [ $hostname != "igarlic" ]; then
    echo "Wrong supervisor hostname $hostname"
    exit 1
fi

memory=$(get_field "$ENDPOINT/processes/1" "memory")

if [ $memory -ne 4178 ]; then
    echo "Wrong process memory metrics $memory"
    exit 1
fi

protocol=$(get_field "$ENDPOINT/processes/1/endpoints/1" "protocol")

if [ $protocol != "udpv6" ]; then
    echo "Wrong process endpoint protocol $protocol"
    exit 1
fi

text=$(get_field "$ENDPOINT/processes/1/console/1" "text")

if [ $text != "Hello" ]; then
    echo "Wrong process console output $text"
    exit 1
fi

exit 0
