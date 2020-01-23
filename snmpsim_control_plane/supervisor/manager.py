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
import subprocess
import time

from snmpsim_control_plane import log
from snmpsim_control_plane.supervisor.reporting.manager import ReportingManager
from snmpsim_control_plane.supervisor import lifecycle


POLL_PERIOD = 1

STATE_ADDED = 'added'
STATE_CHANGED = 'changed'
STATE_RUNNING = 'running'
STATE_REMOVED = 'removed'
STATE_DIED = 'died'


def _traverse_dir(top_dir):
    files = []
    entries = os.listdir(top_dir)

    for entry in entries:
        dir_or_file = os.path.join(top_dir, entry)
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

    started = int(time.time())

    log.info('Watching directory %s' % watch_dir)

    while True:
        # Collect and log processes output

        rlist = {x['pipe'][0]: x['executable']
                 for x in known_instances.values()
                 if x['state'] == STATE_RUNNING}

        while True:
            try:
                r, w, x = select.select(rlist, [], [], 0.1)

            except Exception as exc:
                log.error(exc)
                break

            if not r:
                break

            timestamp = int(time.time())

            for fd in r:
                executable = rlist[fd]
                instance = known_instances[executable]
                console = instance['console']

                log.msg('Output from process "%s" begins' % executable)

                page_text = os.read(fd, console.MAX_CONSOLE_SIZE)
                page_text = page_text.decode(errors='ignore')

                console.add(page_text, timestamp)

                log.msg(page_text)
                log.msg('Output from process "%s" ends' % executable)

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
                    'pid': 0,
                    'executable': fl,
                    'file_info': stat,
                    'leash': None,
                    'pipe': (None, None),
                    'state': STATE_ADDED,
                    'created': time.time(),
                    'started': None,
                    'stopped': None,
                    'runtime': lifecycle.Counter(0),
                    'changes': lifecycle.Counter(0),
                    'exits': lifecycle.Counter(0),
                    'console': lifecycle.ConsoleLog(),
                }
                known_instances[fl] = instance

                log.info('Start tracking executable %s' % fl)

            pid = instance['leash'].pid if instance['leash'] else '?'

            if instance['file_info'] != stat:
                instance['file_info'] = stat
                instance['state'] = STATE_CHANGED
                instance['changes'] += 1

                log.info('Existing executable %s (PID %s) has '
                         'changed' % (fl, pid))

            if instance['state'] == STATE_RUNNING:
                executable = instance['leash']

                executable.poll()

                if executable.returncode is not None:
                    instance['state'] = STATE_DIED
                    instance['stopped'] = time.time()
                    instance['exits'] += 1

                    uptime = int(
                        time.time() - instance['started'] or time.time())

                    log.info(
                        'Executable %s (PID %s) has died '
                        '(rc=%s), uptime %s' % (fl, pid, executable.returncode,
                                                uptime))

            existing_files.add(fl)

        removed_files = set(known_instances) - existing_files

        for fl in removed_files:
            instance = known_instances[fl]
            instance['state'] = STATE_REMOVED
            instance['changes'] += 1

            log.info(
                'Existing executable %s (PID %s) has been '
                'removed' % (fl, instance['pid']))

        for fl, instance in tuple(known_instances.items()):
            state = instance['state']

            if state in (STATE_ADDED, STATE_DIED):
                if state == STATE_DIED:
                    r, w = instance['pipe']

                    try:
                        os.close(r)
                        os.close(w)

                    except OSError as exc:
                        log.error(exc)

                r, w = os.pipe()

                leash = _run_process(fl, w)

                instance['leash'] = leash
                instance['pipe'] = r, w

                if leash:
                    instance['state'] = STATE_RUNNING
                    instance['started'] = time.time()
                    instance['pid'] = leash.pid

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

                r, w = instance['pipe']
                if r:
                    try:
                        os.close(r)
                        os.close(w)

                    except OSError as exc:
                        log.error(exc)

                if state == STATE_CHANGED:
                    instance['state'] = STATE_DIED

                else:
                    known_instances.pop(fl)

                    log.info(
                        'Stopped tracking executable %s' % fl)

            elif state == STATE_RUNNING:
                leash = instance['leash']
                if _process_is_running(leash):
                    now = time.time()
                    instance['runtime'] = lifecycle.Counter(
                        now - instance['created'])

                else:
                    instance['state'] = STATE_DIED
                    instance['exits'] += 1

                    log.info('Executable %s (PID %s) has '
                             'died' % (fl, leash.pid))

        ReportingManager.process_metrics(
            watch_dir, *known_instances.values())

        time.sleep(POLL_PERIOD)
