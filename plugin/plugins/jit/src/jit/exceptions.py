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

"""
Contains exceptions classes for the app plugins.
"""


class EventNotFound(Exception):
    """
    Raised when searched event in XML file is not found.
    """
    pass


class UndefinedSeverity(Exception):
    """
    Raised when a severity specified in XML file is not yet handled.

    The :attr:`args` attribute contains 2-tuple elements where first item is
    severity name, the second item is the event name.
    """
    pass


class FTPError(Exception):
    """
    Raised when there is a problem authenticating to the FTP server to retrieve
    the XML file.

    The :attr:`args` attribute contains 3-tuple elements where first item is the
    host name, the second item is the port number and the third is the login
    used to establish the connection.
    """
    pass


class FTPRetrError(FTPError):
    """
    Raised when there is a problem reading the XML file over FTP.

    The :attr:`args` attribute contains 2-tuple elements where first item is
    an instance of class :class:`ftplib.FTP` for the current FTP session and
    the second item is the location of filename on server side.
    """
    pass


class FTPTimedOut(FTPError):
    """
    Raised when FTP connection timed out.

    The :attr:`args` attribute contains 4-tuple elements where first item is the
    host name, the second item is the port number, third is the login
    used to establish the connection and last is the timeout in seconds.
    """
    pass