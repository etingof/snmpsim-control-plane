#!/bin/bash
#
# Example REST API based SNMP simulator bootstrapping
#
ENDPOINT=http://localhost:5000/snmpsim/mgmt/v1

path="`dirname \"$0\"`"

. $path/functions.sh


# Create a virtual lab
req='{
  "name": "Test Lab"
}'

lab_id=$(create_resource "$req" $ENDPOINT/labs) || exit 1


# Create a SNMP agent
req='{
  "name": "Test SNMP agent",
  "data_dir": "."
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


# Bind SNMP engine to SNMP agent
update_resource $ENDPOINT/agents/$agent_id/engine/$engine_id


# Create SNMP transport endpoint
req='{
  "name": "Test SNMP transport endpoint (UDPv4 at localhost)",
  "protocol": "udpv4",
  "address": "127.0.0.1:1161"
}'

endpoint_id=$(create_resource "$req" $ENDPOINT/endpoints)

# Bind SNMP transport endpoint to SNMP engine
update_resource $ENDPOINT/engines/$engine_id/endpoint/$endpoint_id


# Bind SNMP agent to virtual lab
update_resource $ENDPOINT/labs/$lab_id/agent/$agent_id

# Upload a sample .snmprec file
snmprec_file=/tmp/public.snmprec

cat > $snmprec_file <<EOF
1.3.6.1.2.1.1.1.0|4|Linux zeus 4.8.6.5-smp #2 SMP Sun Nov 13 14:58:11 CDT 2016 i686
1.3.6.1.2.1.1.2.0|6|1.3.6.1.4.1.8072.3.2.10
1.3.6.1.2.1.1.3.0|67:numeric|rate=100,initial=123999999
1.3.6.1.2.1.1.4.0|4|SNMP Laboratories, info@snmplabs.com
1.3.6.1.2.1.1.5.0|4:writecache|value=zeus.snmplabs.com (you can change this!)
1.3.6.1.2.1.1.6.0|4|San Francisco, California, United States
1.3.6.1.2.1.1.7.0|2|72
1.3.6.1.2.1.1.8.0|67:numeric|rate=100,initial=123999999
EOF

upload_recording $ENDPOINT/recordings/public.snmprec $snmprec_file

# Power ON the lab
update_resource $ENDPOINT/labs/$lab_id/power/on
