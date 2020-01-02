#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator management: data simulation recording management
#
import os

from snmpsim_control_plane import log
from snmpsim_control_plane import error


KNOWN_EXTENSIONS = {
    '.snmprec': 'snmprec',
    '.sapwalk': 'sapwalk',
    '.snmpwalk': 'snmpwalk'
}


def _traverse_dir(directory):
    files = []
    entries = os.listdir(directory)

    for entry in entries:
        dir_or_file = os.path.join(directory, entry)
        if os.path.isdir(dir_or_file):
            files.extend(_traverse_dir(dir_or_file))

        else:
            files.append(dir_or_file)

    return files


def get_recording_type(filename):
    for ext in KNOWN_EXTENSIONS:
        if filename.endswith(ext):
            return KNOWN_EXTENSIONS[ext]


def list_recordings(data_dir):

    try:
        files = _traverse_dir(data_dir)

    except Exception as exc:
        raise error.ControlPlaneError(
            'Directory %s traversal failure: %s' % (data_dir, exc))

    recordings = []

    for filename in files:
        stat = os.stat(filename, follow_symlinks=True)

        recording_type = get_recording_type(filename)
        if not recording_type:
            continue

        recording = {
            'path': filename[len(data_dir) + 1:],
            'size': stat.st_size,
            'type': recording_type
        }

        recordings.append(recording)

    return recordings


def get_recording(data_dir, filename, exists=False,
                  not_exists=False, ensure_path=False):
    filename = os.path.abspath(os.path.join(data_dir, filename))

    if not filename.startswith(data_dir):
        log.error('Requested recording %s is outside of data root' % filename)
        raise error.ControlPlaneError('No such recording')

    if exists and not os.path.exists(filename):
        log.error('Requested recording %s does not exist' % filename)
        raise error.ControlPlaneError('No such recording')

    if not_exists and os.path.exists(filename):
        log.error('Requested recording %s unexpectedly exists' % filename)
        raise error.ControlPlaneError('No such recording')

    if ensure_path:
        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)

            except OSError as exc:
                log.error('Failed to create %s: exc' % directory)
                raise error.ControlPlaneError('No such recording')

        elif not os.path.isdir(directory):
            raise error.ControlPlaneError('No such recording')

    return os.path.dirname(filename), os.path.basename(filename)
