# -*- coding: UTF-8 -*-
# Copyright (C) Canux CHENG <canuxcheng@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
This module manage the project documentation.
"""

import os

from fabric.api import env, task, hosts, local, execute
from fabric.contrib.project import rsync_project


DOCROOT = '/var/www/project'
DOCDIR = os.path.join(DOCROOT, 'plugin-app-pdm')


@task
@hosts('canuxcheng.com')
def upload():
    """Upload doc to central server"""
    env.user = 'webcontent'
    rsync_project(DOCDIR, 'doc/_build/html/', delete=True)


@task
def generate():
    """
    Generate the documentation for the project.

    Find the full generated doc in \"doc/_build/html/index.html\".
    """
    local('cd doc && make clean && make html')


@task()
def install():
    """
    Generate and install the documentation online on central server.
    """
    execute(generate)
    execute(upload)
