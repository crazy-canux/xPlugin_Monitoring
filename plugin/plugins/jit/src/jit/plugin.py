# -*- coding: utf-8 -*-
# Copyright (C) Canux <http://www.Company.com/>
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
============================
:mod:`jit.plugin` module
============================

Contains classes that handle plugin creation that make use of XML interface.
"""

# Monitoring imports
from monitoring.nagios.plugin import NagiosPlugin
from monitoring.nagios.plugin import argument

from .exceptions import FTPError
from requests.exceptions import HTTPError
from .session import RemoteInterfaceSession
from .interface import XMLInterface


class XMLInterfacePlugin(NagiosPlugin):
    """
    This is the base class to create a new plugin using the XML interface.
    """
    def initialize(self):
        """
        Plugin initialization. Establish a connection to the remote server.

        Set attribute :attr:`interface` that store the XML interface instance
        and get data from it.
        """
        super(XMLInterfacePlugin, self).initialize()

        # Establish a connection to the remote server provided by --url argument
        remote = RemoteInterfaceSession(self.options.url,
                                        self.options.timeout)
        try:
            remote.connect()
            self.interface = XMLInterface(remote.read_data())
        except FTPError as e:
            self.unknown(e)
        except HTTPError as e:
            self.unknown(e)

    def define_plugin_arguments(self):
        """
        Define extra arguments for this plugin.
        """
        super(XMLInterfacePlugin, self).define_plugin_arguments()

        self.required_args.add_argument(
            '--url',
            dest='url',
            help='URL of the XML interface. Protocol supported can be '
                 'either ftp:// or http://.',
            required=True)

        self.required_args.add_argument(
            '-t', '--timeout',
            dest='timeout',
            type=int,
            default=10,
            help='Connection timeout in seconds (default to 10 secs).')


class XMLStatusCheck(XMLInterfacePlugin):
    """
    Class to check XML interface status.
    """

    def define_plugin_arguments(self):
        """Define extra plugin arguments"""
        super(XMLStatusCheck, self).define_plugin_arguments()

        self.required_args.add_argument(
            '-c', '--critical',
            dest='critical_mins',
            type=argument.minutes,
            help='XML should be updated before this number of minutes.',
            required=True)


class XMLEventPlugin(XMLInterfacePlugin):
    """
    Class to check an event from JIT application via the XML interface and
    returns status back to Nagios.
    """

    def define_plugin_arguments(self):
        """
        Define extra arguments for this plugin.
        """
        super(XMLEventPlugin, self).define_plugin_arguments()

        self.required_args.add_argument(
            '-e', '--event',
            dest='event',
            help='JIT event to check from XML interface.',
            required=True)
