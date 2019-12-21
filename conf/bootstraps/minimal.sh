#!/bin/bash
#
# Example REST API based SNMP simulator bootstrapping
#
ENDPOINT=http://localhost:8000/snmpsim/mgmt/v1

set -x

path="`dirname \"$0\"`"

. $path/functions.sh


# Create a virtual lab
req='{
  "name": "Test Lab"
}'

lab_id=$(create_resource "$req" $ENDPOINT/labs)


# Create a SNMP agent
req='{
  "name": "Test SNMP agent",
  "data_dir": "data"
}'

agent_id=$(create_resource "$req" $ENDPOINT/agents)


# Create a SNMP engine
req='{
  "name": "Test SNMP engine"
}'

engine_id=$(create_resource "$req" $ENDPOINT/engines)


# Create SNMP USM user
req='{
  "name": "Test SNMP USM user (no crypto)",
  "user": "simulator"
}'

user_id=$(create_resource "$req" $ENDPOINT/users)


# Bind SNMP USM user to SNMP engine
update_resource $ENDPOINT/engines/$engine_id/user/$user_id


# Create SNMP transport endpoint
req='{
  "name": "Test SNMP transport endpoint (UDPv4 at localhost)",
  "domain": "udpv4",
  "address": "127.0.0.1:1161"
}'

endpoint_id=$(create_resource "$req" $ENDPOINT/endpoints)


# Bind SNMP transport endpoint to SNMP engine
update_resource $ENDPOINT/engines/$engine_id/endpoint/$endpoint_id

# Power ON the lab
update_resource $ENDPOINT/labs/$lab_id/power/on
