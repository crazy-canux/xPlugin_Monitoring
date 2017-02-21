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

import subprocess
from datetime import datetime
from nagios.errorlevels import NagiosUnknown

# Plugin configuration
import config


#-------------------------------------------------------------------------------
# Exceptions
#-------------------------------------------------------------------------------

class LmxStatusError(Exception):
    """
    Exception raised when lmxendutil encounter an error
    """

    def __init__(self, error_msg, retcode, license):
        self.errmsg = error_msg
        self.retcode = retcode
        self.license = license


#-------------------------------------------------------------------------------
# Lmx classes
#-------------------------------------------------------------------------------

class Feature(object):
    """
    Store data about a feature: name, used licenses and total.
    """

    def __init__(self, name, used_licenses, total_licenses, expire_date):
        self.name = name

        try:
            self.used_licenses = long(used_licenses)
            self.total_licenses = long(total_licenses)
            self.expires = datetime.strptime(expire_date, '%Y-%m-%d')
        except ValueError as e:
            raise NagiosUnknown('Exception: %s' % e)

    def __str__(self):
        """Print feature data as text to be used in Nagios long output."""
        return '{0:>s}: {1:d} / {2:d}'.format(self.name,
                                              self.used_licenses,
                                              self.total_licenses)

    def print_perfdata(self):
        """Print feature performance data string."""
        return '\'{0:>s}\'={1:d};;;0;{2:d}'.format(self.name,
                                                   self.used_licenses,
                                                   self.total_licenses)


class Features(object):
    """
    This class stores all features objects. She is able to compute some
    global stats about licenses usage.
    """

    today_date = datetime.today()

    # Class customization
    def __init__(self):
        self.features = []

    def __iter__(self):
        return iter(self.features)

    def __len__(self):
        return len(self.features)
    
    def __setitem__(self, key, value):
        self.features[key] = value

    def __getitem__(self, key):
        return self.features[key]

    def __str__(self):
        """
        Return the Nagios output when all is OK.
        """
        return 'LM-X: usage: %d / %d license(s) available.' % (
            self.calc_used_licenses(), self.calc_total_licenses())

    # Public methods
    def append(self, value):
        """
        Lists append-like
        """
        self.features.append(value)

    def calc_total_licenses(self):
        """
        Calculate the total number of available licenses for all features.
        """
        total = 0
        for feature in self:
            total += feature.total_licenses
        return total

    def calc_used_licenses(self):
        """
        Calculate the total number of used licenses.
        """
        in_use = 0
        for feature in self:
            in_use += feature.used_licenses
        return in_use

    def calc_expired_license(self):
        """
        Return a dictionnary with the feature name as the key and a tuple
        (days_before_expiration, expiration_date).
        """
        remains = 0
        expire_list = {}
        for feature in self:
            td = feature.expires - Features.today_date
            if td.days < 0:
                remains = 0
            else:
                remains = td.days
            expire_list[feature.name] = (remains, feature.expires)
        return expire_list

    def print_perfdata(self):
        """
        Construct and return the perfdata string for all features.
        """
        perfdatas = [' |']
        for feature in self:
            perfdatas.append(feature.print_perfdata())
        return " ".join(perfdatas)


#-------------------------------------------------------------------------------
# Lmx functions
#-------------------------------------------------------------------------------

def status_xml(remote_host, license_port):
    """
    Execute a 'lmxendutil' command on a remote server. Return results as XML.
    """

    cmdline = [config.LMXENDUTIL_PATH,
               "-licstatxml",
               "-host", remote_host,
               '-port', license_port]

    cmd = subprocess.Popen(cmdline,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    cmd_output = cmd.communicate()[0]

    if cmd.returncode:
        raise LmxStatusError("Unexpected error !",
                             cmd.returncode, '%s@%s' % (license_port,
                                                        remote_host))

    # Make output to be XML. Remove first 3 lines that includes software name
    # and copyright informations.
    xml_data = "\n".join(cmd_output.split('\n')[3:])

    return xml_data