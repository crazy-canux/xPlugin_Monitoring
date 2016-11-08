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
:mod:`jit.session` module
============================

Contains classes that handle session connection to fetch XML interface
content remotly.
"""

import logging
import urlparse
import socket
import ftplib

from StringIO import StringIO

import exceptions
import requests

logger = logging.getLogger('plugin.jit.session')


class RemoteInterfaceSession(object):
    """
    Remote session handling to fetch XML interface content.
    """
    def __init__(self, url, timeout=10):
        """
        Initialize a new remote session on ``url``. Raise an error if
        ``timeout` in seconds is reached.

        >>> session = RemoteInterfaceSession(\
                "http://insalert.app.corp:80/insequence/Alert_USMSMSQL0001.xml")
        >>> session.protocol
        'http'
        >>> session.hostname
        'insalert.app.corp'
        >>> session.port
        80
        >>> session.path
        '/insequence/Alert_USMSMSQL0001.xml'

        :param url: Valid URL scheme.
        :type url: basestring
        """
        self._url = urlparse.urlparse(url)

        self.protocol = self._url.scheme
        self.timeout = timeout
        self.hostname = self._url.hostname
        self.port = self._url.port
        self.path = self._url.path
        self.query = self._url.query
        self.username = getattr(self._url, "username", None)
        self.password = getattr(self._url, "password", None)

        self._remote = None

    def connect(self):
        """
        Establish the remote connection.

        # FTP session
        >>> session = RemoteInterfaceSession(\
            "ftp://Nagios:Company1+@10.88.11.21:4000/ALERT_BEGNESEQ0001.xml")
        >>> session.connect()
        >>> isinstance(session._remote, ftplib.FTP)
        True

        # HTTP session
        >>> session = RemoteInterfaceSession(\
                "http://insalert.app.corp:80/insequence/Alert_USMSMSQL0001.xml")
        >>> session.connect()
        >>> session._remote
        <Response [200]>

        # Error
        >>> session = RemoteInterfaceSession(\
            "gopher://insalert.app.corp:80/insequence/Alert_USMSMSQL0001.xml")
        >>> session.connect()
        Traceback (most recent call last):
            ...
        NotImplementedError: Only HTTP or FTP are supported !
        """
        logger.debug("Remote session uses %s." % self.protocol.upper())

        if self.protocol == "ftp":
            self._remote = ftplib.FTP()
            try:
                self._remote.connect(self.hostname,
                                     self.port,
                                     self.timeout)
                if self.username and self.password:
                    self._remote.login(self.username, self.password)
                else:
                    self._remote.login()
            except socket.timeout:
                raise exceptions.FTPTimedOut("Timeout on FTP server %s !" %
                                             self.hostname)
            except:
                raise exceptions.FTPError(self.hostname,
                                          self.port,
                                          self.username)
            logger.debug('Successfully authenticated on FTP server.')
        elif self.protocol == "http":
            if self.username and self.password:
                credentials = (self.username, self.password)
            else:
                credentials = None

            url = "{0.protocol}://{0.hostname}{0.path}?{0.query}"
            self._remote = requests.get(url.format(self), auth=credentials)
            self._remote.raise_for_status()
            logger.debug('Successfully authenticated on HTTP server.')
        else:
            raise NotImplementedError("Only HTTP or FTP are supported !")

    def read_data(self):
        """
        Returns the XML data as a file-like object (StringIO).

        # FTP session
        >>> session = RemoteInterfaceSession(\
            "ftp://Nagios:Company1+@10.88.11.21:4000/ALERT_BEGNESEQ0001.xml")
        >>> session.connect()
        >>> data = session.read_data()
        >>> "<?xml" in data
        True

        # HTTP session
        >>> session = RemoteInterfaceSession(\
                "http://insalert.app.corp:80/insequence/Alert_USMSMSQL0001.xml")
        >>> session.connect()
        >>> data = session.read_data()
        >>> "USMSMSQL0001" in data
        True
        """
        data = StringIO()

        if isinstance(self._remote, ftplib.FTP):
            try:
                self._remote.retrlines('RETR %s' % self.path, data.write)
            except ftplib.all_errors as e:
                raise exceptions.FTPRetrError(
                    "Cannot read the XML data over FTP: %s" % e)
        elif isinstance(self._remote, requests.Response):
            data.write(self._remote.text)

        return data.getvalue()
