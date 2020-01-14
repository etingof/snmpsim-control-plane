#
# This file is part of snmpsim-control-plane software.
#
# Copyright (c) 2019-2020, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim-control-plane/license.html
#
"""SNMP Simulator Control Plane

REST API driven management and monitoring supervisor to
remotely operate SNMP simulator.
"""
import os
import sys

import setuptools

classifiers = """\
Development Status :: 4 - Beta
Environment :: Console
Intended Audience :: Developers
Intended Audience :: Information Technology
Intended Audience :: System Administrators
Intended Audience :: Telecommunications Industry
License :: OSI Approved :: BSD License
Natural Language :: English
Operating System :: OS Independent
Programming Language :: Python :: 2
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.2
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Topic :: Communications
Topic :: System :: Monitoring
Topic :: System :: Networking :: Monitoring
"""

if sys.version_info[:2] < (2, 7):
    print("ERROR: this package requires Python 2.7 or later!")
    sys.exit(1)

with open(os.path.join('snmpsim_control_plane', '__init__.py')) as fl:
    version = fl.read().split('\'')[1]

# make sure to have fresh `setuptools` for this to work
with open('requirements.txt') as fl:
    requirements = fl.readlines()

doclines = [x.strip() for x in (__doc__ or '').split('\n') if x]

params = {
    'name': 'snmpsim-control-plane',
    'version': version,
    'description': doclines[0],
    'long_description': ' '.join(doclines[1:]),
    'maintainer': 'Ilya Etingof <etingof@gmail.com>',
    'author': 'Ilya Etingof',
    'author_email': 'etingof@gmail.com',
    'url': 'http://snmplabs.com/snmpsim-control-plane',
    'license': 'BSD',
    'platforms': ['any'],
    'classifiers': [x for x in classifiers.split('\n') if x],
    'packages': setuptools.find_packages(),
    'entry_points': {
        'console_scripts': [
            'snmpsim-mgmt-restapi = snmpsim_control_plane.commands.management:main',
            'snmpsim-mgmt-supervisor = snmpsim_control_plane.commands.supervisor:main',
            'snmpsim-metrics-importer = snmpsim_control_plane.commands.importer:main',
            'snmpsim-metrics-restapi = snmpsim_control_plane.commands.metrics:main',
        ]
    },
    'install_requires': requirements,
    'zip_safe': False,  # Flask
    'include_package_data': True
}

setuptools.setup(**params)
