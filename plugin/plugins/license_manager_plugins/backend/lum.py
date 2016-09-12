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

import re
import subprocess
import os
from nagios.errorlevels import NagiosOk, NagiosUnknown

# Plugin configuration
import config

#-------------------------------------------------------------------------------
# Exceptions
#-------------------------------------------------------------------------------
class LumStatusError(Exception):
    """Exception raised when i4* command encounter an error"""
    def __init__(self, error_msg, retcode, license):
        self.errmsg = error_msg
        self.retcode = retcode
        self.license = license

#-------------------------------------------------------------------------------
# LUM related
#-------------------------------------------------------------------------------
def status(ini_file_location):
    """Check the status of LUM
    Set IFOR_CONFIG env variable and execute 'i4tv' command"""
    cmdline = [config.I4TV_PATH]
    # Ini file exist ?
    if not os.path.exists(ini_file_location):
        raise NagiosUnknown("INI file not found: '{0}'".format(ini_file_location))
    # Create environment variable for i4* commands
    os.putenv("IFOR_CONFIG", ini_file_location)

    cmd = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    cmd_output = cmd.communicate()[0]

    # Check if i4* command is successful
    done_pattern = re.compile(r"Completed license transaction.*")
    done_match = done_pattern.search(cmd_output)
    if not done_match:
        raise LumStatusError("Error occured when checking for LUM !", cmd.returncode, os.path.basename(ini_file_location))
    
    return cmd_output.split('\n')

#def expiration(license_port):
#    """Execute a 'lstc_qrun -r -s' command using lstc_qrun on a remote server"""
#    cmdline = [config.I4TV_PATH, "-r", "-s", license_port]
#
#    cmd = subprocess.Popen(cmdline, stdout=subprocess.PIPE)
#    cmd_output = cmd.communicate()[0].split('\n')
#
#    # Check return code
#    if cmd.returncode != 0:
#        # Get error message
#        error_pattern = re.compile('.*ERROR (.*)')
#        error_match = error_pattern.search(cmd_output[-1])
#        if error_match: error_message = error_match.group(1).title()
#        else: error_message = "License server not available !"
#        raise LumStatusError(error_message, cmd.returncode, license_port)
#
#    return cmd_output
