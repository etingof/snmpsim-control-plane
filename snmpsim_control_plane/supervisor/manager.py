#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP Agent Simulator Control Plane: process management
#
import os
import select
import time
import subprocess

from snmpsim_control_plane import log

POLL_PERIOD = 1

STATE_ADDED = 'added'
STATE_CHANGED = 'changed'
STATE_RUNNING = 'running'
STATE_REMOVED = 'removed'
STATE_DIED = 'died'


def _traverse_dir(dir):
    files = []
    entries = os.listdir(dir)

    for entry in entries:
        dir_or_file = os.path.join(dir, entry)
        if os.path.isdir(dir_or_file):
            files.extend(_traverse_dir(dir_or_file))

        else:
            if os.access(dir_or_file, os.X_OK):
                files.append(dir_or_file)

    return files


def _run_process(fl, fd):
    try:
        return subprocess.Popen(
            [fl], stdout=fd, stderr=fd)

    except Exception as exc:
        log.error('Executable %s failed to start: %s' % (fl, exc))


def _kill_process(leash):
    leash.terminate()

    time.sleep(3)

    if leash.returncode is None:
        log.error(
            'Process %s did not stop gracefully, killing...' % leash.pid)
        leash.kill()
        leash.wait()


def _process_is_running(leash):
    if leash:
        leash.poll()
        return leash.returncode is None


def manage_executables(watch_dir):
    known_instances = {}

    log.info('Watching directory %s' % watch_dir)

    while True:
        # Collect and log processes output

        rlist = {x['pipe']: x['executable'] for x in known_instances.values()}

        while True:
            r, w, x = select.select(rlist, [], [], 0.1)
            if not r:
                break

            for fd in r:
                log.msg('Output from process "%s" begins' % rlist[fd])
                log.msg(os.read(fd, 32768).decode(errors='ignore'))
                log.msg('Output from process "%s" ends' % rlist[fd])

        # Watch executables

        existing_files = set()

        try:
            files = _traverse_dir(watch_dir)

        except Exception as exc:
            log.error('Directory %s traversal failure: %s' % (watch_dir, exc))
            time.sleep(10)
            continue

        for fl in files:
            instance = known_instances.get(fl)

            stat = os.stat(fl).st_mtime

            if not instance:
                instance = {
                    'executable': fl,
                    'file_info': stat,
                    'leash': None,
                    'pipe': None,
                    'state': STATE_ADDED,
                    'started': None,
                }
                known_instances[fl] = instance

                log.info('Start tracking executable %s' % fl)

            pid = instance['leash'].pid if instance['leash'] else '?'

            if instance['file_info'] != stat:
                instance['file_info'] = stat
                instance['state'] = STATE_CHANGED

                log.info(
                    'Existing executable %s (PID %s) has changed' % (fl, pid))

            if instance['state'] == STATE_RUNNING:
                process = instance['leash']

                process.poll()

                if process.returncode is not None:
                    instance['state'] = STATE_DIED

                    log.info(
                        'Executable %s (PID %s) has died '
                        '(rc=%s)' % (fl, pid, process.returncode))

            existing_files.add(fl)

        removed_files = set(known_instances) - existing_files

        for fl in removed_files:
            instance = known_instances[fl]
            instance['state'] = STATE_REMOVED

            log.info(
                'Existing executable %s (PID %s) has been removed' % (fl, pid))

        for fl, instance in tuple(known_instances.items()):
            state = instance['state']

            if state in (STATE_ADDED, STATE_DIED):
                r, w = os.pipe()

                leash = _run_process(fl, w)

                instance['leash'] = leash
                instance['pipe'] = r

                if leash:
                    instance['state'] = STATE_RUNNING
                    instance['started'] = time.time()

                    log.info(
                        'Executable %s (PID %s) has been '
                        'started' % (fl, leash.pid))

            elif state in (STATE_CHANGED, STATE_REMOVED):
                leash = instance['leash']

                if leash:
                    _kill_process(leash)

                    log.info(
                        'Executable %s (PID %s) has been '
                        'stopped' % (fl, leash.pid))

                r = instance['pipe']
                if r:
                    os.close(r)

                known_instances.pop(fl)

                log.info(
                    'Stopped tracking executable %s' % fl)

            elif state == STATE_RUNNING:
                leash = instance['leash']
                if not _process_is_running(leash):
                    instance['state'] = STATE_DIED

                    uptime = int(
                        time.time() - instance['started'] or time.time())

                    log.info(
                        'Executable %s (PID %s) has died, uptime %s '
                        'secs' % (fl, leash.pid, uptime))

        time.sleep(POLL_PERIOD)
