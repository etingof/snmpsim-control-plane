#!/bin/bash
#
# Stand up SNMP simulator command responder management REST API,
# issue a series of REST API calls to build complete SNMP simulator
# configuration.
#
# Fail the entire script on any failure.
#

set -e

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

restapi_conf=$(mktemp $repo_root/.tmp/mgmt-restapi.XXXXXX)
dst_dir=$(mktemp -d $repo_root/.tmp/snmpsimd.XXXXXX)
data_dir=$(mktemp -d $repo_root/.tmp/snmpsimd.XXXXXX)

cat << END_OF_CONFIG > $restapi_conf
SQLALCHEMY_DATABASE_URI = "sqlite:///$repo_root/.tmp/snmpsim-mgmt-restapi.db"
SQLALCHEMY_ECHO = False
SQLALCHEMY_TRACK_MODIFICATIONS = False
DEBUG = False

SNMPSIM_MGMT_LISTEN_IP = '127.0.0.1'
SNMPSIM_MGMT_LISTEN_PORT = 5000

SNMPSIM_MGMT_SSL_CERT = None
SNMPSIM_MGMT_SSL_KEY = None
SNMPSIM_MGMT_DATAROOT = "$data_dir"
SNMPSIM_MGMT_TEMPLATE = 'snmpsim-command-responder.j2'
SNMPSIM_MGMT_DESTINATION = "$dst_dir"

END_OF_CONFIG

cat $restapi_conf

snmpsim-mgmt-restapi \
    --config $restapi_conf \
    --recreate-db

snmpsim-mgmt-restapi \
    --config $restapi_conf &

restapi_pid=$!

function cleanup()
{
    rm -fr $repo_root/.tmp
    kill $restapi_pid && true
}

trap cleanup EXIT

sleep 5

if [ $run_tests = "yes" ]; then
    $repo_root/conf/bootstraps/minimal.sh

    if [ ! -f $dst_dir/snmpsim-run-labs.sh ]; then
        echo "Empty/none snmpsim-run-labs.sh generated"
        exit 1
    fi
fi

if [ $keep_running = "yes" ]; then
    cat -
fi

exit 0
