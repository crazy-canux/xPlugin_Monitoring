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

"""Powershell related module."""

from datetime import datetime

from bs4 import BeautifulSoup

from .exceptions import XMLValidityError


class BaseXML(object):
    """Base class for Powershell XML result handling.

    :param xml: XML file handle or string.
    :type xml: str, unicode, file
    """
    supported_versions = (
        '1.1.0.1',
    )

    def __init__(self, xml):
        if isinstance(xml, (str, unicode, file)):
            # Create the parser
            self.xml = BeautifulSoup(xml)

            # Check XML validity
            root = getattr(self.xml, 'objs', None)
            if root:
                try:
                    self.version = root['version']
                    self.schema = root['xmlns']

                    try:
                        self._timestamp = float(root.s.string.split(',')[0])
                    except (ValueError, TypeError):
                        raise XMLValidityError(
                            "Cannot determine XML timestamp !")
                except (KeyError, AttributeError):
                    raise XMLValidityError("Cannot determine XML version, "
                                           "schema and timestamp !")

                # Test supported version
                if not self.version in BaseXML.supported_versions:
                    raise XMLValidityError(
                        "XML version \"{version}\" is not "
                        "supported !".format(version=self.version))

                # XML last modified date
                self.last_modified = datetime.fromtimestamp(self._timestamp)
            else:
                raise XMLValidityError("No <objs> root tag !")
        else:
            raise TypeError('Argument "xml" must be an instance of '
                            'str, unicode or file !')
