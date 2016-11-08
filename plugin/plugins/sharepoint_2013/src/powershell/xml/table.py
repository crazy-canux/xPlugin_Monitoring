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

"""Module to represents a Powershell XML result as a table."""

import re

from .base import BaseXML
from .exceptions import XMLValidityError


class XMLTable(BaseXML):
    """
    Represents as a table the XML results from Powershell XML export cmdlet.

    :param xml: XML file handle or string.
    :type xml: str, unicode, file
    """
    def __init__(self, xml):
        super(XMLTable, self).__init__(xml)
        if self.columns and self._entries:
            self._table = self._build_table()
        else:
            raise XMLValidityError('No tabular data found !')

    @property
    def columns(self):
        """Returns the list of available column names in the table."""
        return [c.string for c in self.xml.find_all('s', n='ItemXPath')]

    @property
    def _entries(self):
        """Returns the list of all entries in the table."""
        return [e.string for e in self.xml.find_all('s', n='Value')]

    def _build_table(self):
        """
        Build the table.

        Each entries is a dict with ``{column: value}``.
        """
        table = []
        index = 0
        entry = {}
        num_cols = len(self.columns)

        for value in self._entries:
            column = self.columns[index]

            entry.update({column: value})
            index = (index + 1) % num_cols

            if index == 0:
                table.append(entry)
                entry = {}

        return table

    def match(self, column, regex, invert=False):
        """
        Match for ``regex`` in ``column`` name. The match can be inverted
        setting ``invert`` to true, useful to where a test has failed::

            # Returns all entries dict where the result is not a success.
            match('Result', r'^Success$', invert=True)

        :returns: a list of the dict entries found.
        """
        try:
            pattern = re.compile(regex)
        except re.error:
            raise

        results = []
        for result in self:
            if pattern.match(result[column]):
                if not invert:
                    results.append(result)
            else:
                if invert:
                    results.append(result)
        return results

    def __iter__(self):
        """Iterate over entries."""
        return self._table.__iter__()

    def __repr__(self):
        """Object representation as text."""
        return repr(self._table)
