# -*- coding: utf-8 -*-
# Copyright (C) Faurecia <http://www.faurecia.com/>
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

# TODO: Check how to group status() and expiration() as a single function.

import re
import subprocess
from nagios.errorlevels import NagiosOk

# Plugin configuration
import config

#-------------------------------------------------------------------------------
# Exceptions
#-------------------------------------------------------------------------------
class LstcStatusError(Exception):
    """Exception raised when lstc_qrun encounter an error"""
    def __init__(self, error_msg, retcode, license):
        self.errmsg = error_msg
        self.retcode = retcode
        self.license = license

#-------------------------------------------------------------------------------
# Lstc related
#-------------------------------------------------------------------------------
def status(license_port):
    """Execute a 'lstc_qrun -s' command using lstc_qrun on a remote server"""
    cmdline = [config.LSTCQRUN_PATH, "-s", license_port]
    
    cmd = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    cmd_output = cmd.communicate()[0]

    # Warn for error message if any
    error_pattern = re.compile('.*ERROR (.*)')
    error_match = error_pattern.search(cmd_output)
    if error_match:
        error_message = error_match.group(1)
        raise LstcStatusError(error_message, cmd.returncode, license_port)

    # Check return code
    if cmd.returncode == 0:
        raise NagiosOk("There is no program running or queued.")
    
    return cmd_output.split('\n')

def expiration(license_port):
    """Execute a 'lstc_qrun -r -s' command using lstc_qrun on a remote server"""
    cmdline = [config.LSTCQRUN_PATH, "-r", "-s", license_port]
    
    cmd = subprocess.Popen(cmdline, stdout=subprocess.PIPE)
    cmd_output = cmd.communicate()[0].split('\n')
    
    # Check return code
    if cmd.returncode != 0:
        # Get error message
        error_pattern = re.compile('.*ERROR (.*)')
        error_match = error_pattern.search(cmd_output[-1])
        if error_match: error_message = error_match.group(1).title()
        else: error_message = "License server not available !"
        raise LstcStatusError(error_message, cmd.returncode, license_port)
    
    return cmd_output
