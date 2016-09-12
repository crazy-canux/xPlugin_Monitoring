# -*- coding: UTF-8 -*-
#===============================================================================
# Author        : Vincent BESANCON <besancon.vincent@gmail.com>
# Description   : fabric tasks
#-------------------------------------------------------------------------------
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#===============================================================================

"""
This module manage the project documentation.
"""

import os

from fabric.api import *
from fabric.contrib.project import rsync_project


DOCROOT = '/var/www/project'
DOCDIR = os.path.join(DOCROOT, 'jit-plugins')

@task
@hosts('monitoring-dc.app.corp')
def upload():
    """Upload doc to central server"""
    env.user = 'webcontent'
    rsync_project(DOCDIR, 'docs/build/html/', delete=True)

@task
def generate():
    """
    Generate the documentation for the project.

    Find the full generated doc in \"docs/build/html/index.html\".
    """
    local('cd docs && make clean && make html')

@task()
def install():
    """
    Generate and install the documentation online on central server.
    """
    execute(generate)
    execute(upload)

