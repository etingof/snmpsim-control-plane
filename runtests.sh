#!/bin/bash
#
# Stand up SNMP simulator command responder management REST API,
# issue a series of REST API calls to build complete SNMP simulator
# configuration.
#
# Fail the entire script on any failure.
#

set -e

RESTAPI_CONF=$(mktemp /tmp/snmpsimd.XXXXXX)

sed -e 's/DEBUG = True/DEBUG = False/g' $(pwd)/conf/snmpsim-management.conf > $RESTAPI_CONF

snmpsim-mgmt-restapi \
    --config $RESTAPI_CONF \
    --recreate-db

RESTAPI_DST_DIR=$(mktemp -d /tmp/snmpsimd.XXXXXX)

snmpsim-mgmt-restapi \
    --config $RESTAPI_CONF \
    --destination "$RESTAPI_DST_DIR" &

RESTAPI_PID=$!

function cleanup()
{
    rm -fr "$RESTAPI_DST_DIR" $RESTAPI_CONF
    kill $RESTAPI_PID && exit 0
}

trap cleanup EXIT

sleep 10

bash conf/bootstraps/minimal.sh

[ -z RESTAPI_DST_DIR/snmpsim-run-labs.sh ] && {
    echo "Empty/none `snmpsim-run-labs.sh` generated"; exit 1 ; }
