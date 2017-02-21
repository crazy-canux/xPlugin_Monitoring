# -*- coding: utf-8 -*-
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

# TODO: Check how to group status() and expiration() as a single function.

import re
import subprocess

# Plugin configuration
import config


#-------------------------------------------------------------------------------
# Exceptions
#-------------------------------------------------------------------------------
class FlexlmStatusError(Exception):
    """Exception raised when lmutil encounter an error"""
    def __init__(self, error_msg, retcode, license):
        self.errmsg = error_msg
        self.retcode = retcode
        self.license = license


#-------------------------------------------------------------------------------
# FlexLM related
#-------------------------------------------------------------------------------
def status(license_port, timeout="30", with_stat=False):
    """Execute a 'lmstat -a' command using lmutil on a remote server"""
    cmdline = [config.LMUTIL_PATH, "lmstat", "-t", timeout, "-c", license_port]
    if with_stat:
        cmdline.append('-a')
    
    cmd = subprocess.Popen(cmdline, stdout=subprocess.PIPE)
    cmd_output = cmd.communicate()[0].split('\n')
    
    # Check return code
    if cmd.returncode != 0:
        # Get error message
        error_pattern = re.compile('Error getting status: (.*). \(.*\)')
        error_match = error_pattern.search(cmd_output[-1])
        if error_match: error_message = error_match.group(1).title()
        else: error_message = "License server not available !"
        raise FlexlmStatusError(error_message, cmd.returncode, license_port)
    
    return cmd_output


def expiration(license_port, timeout=60):
    """Execute a 'lmstat -i' command using lmutil on a remote server"""
    cmdline = [config.LMUTIL_PATH, "lmstat", "-t", timeout, "-c", license_port, '-i']
    
    cmd = subprocess.Popen(cmdline, stdout=subprocess.PIPE)
    cmd_output = cmd.communicate()[0].split('\n')
    
    # Check return code
    if cmd.returncode != 0:
        # Get error message
        error_pattern = re.compile('Error getting status: (.*). \(.*\)')
        error_match = error_pattern.search(cmd_output[-1])
        if error_match: error_message = error_match.group(1).title()
        else: error_message = "License server not available !"
        raise FlexlmStatusError(error_message, cmd.returncode, license_port)
    
    return cmd_output
