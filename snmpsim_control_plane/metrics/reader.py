#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator Control Plane: metrics files reader
#
import os
import json
import time

from snmpsim_control_plane import log
from snmpsim_control_plane.metrics import manager

POLL_PERIOD = 10


def _traverse_dir(dir):
    files = []
    entries = os.listdir(dir)

    for entry in entries:
        dir_or_file = os.path.join(dir, entry)
        if os.path.isdir(dir_or_file):
            files.extend(_traverse_dir(dir_or_file))

        else:
            files.append(dir_or_file)

    return files


def watch_metrics(watch_dir):

    log.info('Watching directory %s' % watch_dir)

    while True:

        try:
            files = _traverse_dir(watch_dir)

        except Exception as exc:
            log.error('Directory %s traversal failure: %s' % (watch_dir, exc))
            time.sleep(10)
            continue

        for filename in files:

            log.info('Processing %s' % filename)

            try:
                with open(filename) as fl:
                    jsondoc = json.loads(fl.read())

            except Exception as exc:
                log.error('Error reading file %s: %s' % (filename, exc))
                continue

            finally:
                os.unlink(filename)

            try:
                manager.import_metrics(jsondoc)

            except Exception as exc:
                log.error('Error processing file %s: %s' % (filename, exc))
                continue

        time.sleep(POLL_PERIOD)
