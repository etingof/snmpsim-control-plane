#
# This file is part of SNMP simulator Control Plane software.
#
# Copyright (c) 2019, Ilya Etingof <etingof@gmail.com>
# License: http://snmplabs.com/snmpsim/license.html
#
# SNMP simulator management: configuration renderer
#
import os
import tempfile

import jinja2


def render_configuration(dst_file, template, context):
    search_path = [
        os.path.join(os.path.dirname(__file__), 'templates')]

    if os.path.sep in template:
        search_path.insert(0, os.path.dirname(template))

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(search_path),
        trim_blocks=True, lstrip_blocks=True)

    tmpl = env.get_template(template)

    text = tmpl.render(context=context)

    with tempfile.NamedTemporaryFile(
            dir=os.path.dirname(dst_file), delete=False) as fp:
        fp.write(text)

    os.rename(fp.name, dst_file)
