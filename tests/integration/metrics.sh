#!/bin/bash
#
# Stand up SNMP simulator command responder metrics REST API
# along with metrics collector. Feed the latter a sample metrics
# report and issue a series of REST API calls to make sure metrics
# showed up in REST API endpoints.
#
# Fail the entire script on any failure.
#
endpoint=http://localhost:5001/snmpsim/metrics/v1

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

USAGE=$(
cat << END_OF_USAGE
Usage: $0 [options]
  --help                          Usage help message
  --run-tests                     Run end-to-end tests
  --keep-running                  Keep REST API server running
  --repo-root                     Root directory of package repo
END_OF_USAGE
)

keep_running=no
run_tests=no
repo_root=$(pwd)

POSITIONAL=()
while [[ $# -gt 0 ]]
do
    key="$1"

    case $key in
        --help)
            echo Synopsis: invoke REST API server, optionally initialize
            echo the underlying DB.
            echo "$USAGE"
            exit 0
            ;;
        --repo-root)
            repo_root=$2
            shift # past argument
            shift # past value
            ;;
        --run-tests)
            run_tests=yes
            shift # past argument
            ;;
        --keep-running)
            keep_running=yes
            shift # past argument
            ;;
    esac
done

mkdir -p $repo_root/.tmp

restapi_conf=$(mktemp $repo_root/.tmp/metrics-restapi.XXXXXX)
dst_dir=$(mktemp -d $repo_root/.tmp/snmpsimd.XXXXXX)
data_dir=$(mktemp -d $repo_root/.tmp/snmpsimd.XXXXXX)

cat << END_OF_CONFIG > $restapi_conf
SQLALCHEMY_DATABASE_URI = "sqlite:///$repo_root/.tmp/snmpsim-metrics-restapi.db"
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = False
DEBUG = False

SNMPSIM_MGMT_LISTEN_IP = '127.0.0.1'
SNMPSIM_MGMT_LISTEN_PORT = 5001

END_OF_CONFIG

snmpsim-metrics-restapi \
    --config $restapi_conf \
    --recreate-db

restapi_watch_dir=$(mktemp -d $repo_root/.tmp/snmpsim-metrics.XXXXXX)

snmpsim-metrics-restapi \
    --config $restapi_conf &

RESTAPI_PID=$!

snmpsim-metrics-importer \
    --config $restapi_conf \
    --watch-dir $restapi_watch_dir &

IMPORTER_PID=$!

function cleanup()
{
    rm -fr "$restapi_watch_dir" restapi_conf
    kill $IMPORTER_PID $RESTAPI_PID && true
}

trap cleanup EXIT

sleep 5

if [ $run_tests = "yes" ]; then

    cp $repo_root/tests/integration/samples/*.json $restapi_watch_dir
    
    sleep 10
    
    if compgen -G "$restapi_watch_dir/*"; then
        echo "Metrics not consumed"
        exit 1
    fi
    
    total=$(get_field "$endpoint/activity/packets" "total")
    
    if [ $total -ne 12728 ]; then
        echo "Wrong total packet count $total"
        exit 1
    fi
    
    pdus=$(get_field "$endpoint/activity/messages" "pdus")
    
    if [ $pdus -ne 12728 ]; then
        echo "Wrong total pdus count $pdus"
        exit 1
    fi
    
    var_binds=$(get_field "$endpoint/activity/messages" "var_binds")
    
    if [ $var_binds -ne 14196 ]; then
        echo "Wrong total var_binds count $var_binds"
        exit 1
    fi
    
    failures=$(get_field "$endpoint/activity/messages" "failures")
    
    if [ $failures -ne 0 ]; then
        echo "Wrong total failures count $failures"
        exit 1
    fi
    
    hostname=$(get_field "$endpoint/supervisors/1" "hostname")
    
    if [ $hostname != "igarlic" ]; then
        echo "Wrong supervisor hostname $hostname"
        exit 1
    fi
    
    memory=$(get_field "$endpoint/processes/1" "memory")
    
    if [ $memory -ne 4178 ]; then
        echo "Wrong process memory metrics $memory"
        exit 1
    fi
    
    protocol=$(get_field "$endpoint/processes/1/endpoints/1" "protocol")
    
    if [ $protocol != "udpv4" -a  $protocol != "udpv6" ]; then
        echo "Wrong process endpoint protocol $protocol"
        exit 1
    fi
    
    text=$(get_field "$endpoint/processes/1/console/1" "text")
    
    if [ $text != "Hello" ]; then
        echo "Wrong process console output $text"
        exit 1
    fi

fi

if [ $keep_running = "yes" ]; then
    echo "You can now put your JSON metrics into $restapi_watch_dir for processing"
    cat -
fi

exit 0
