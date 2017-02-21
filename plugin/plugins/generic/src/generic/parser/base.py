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

"""
Parser base class.
"""

from generic.parser.exceptions import RawValueNameError


class BaseParser(object):
    """
    Base class for a new parser.
    """
    def __init__(self):
        self.longoutput = []
        self._raw_value = {}

    @property
    def print_longoutput(self):
        return "\n".join(self.longoutput)

    @property
    def value_keys(self):
        return self._raw_value.keys()

    def _add_longoutput(self, ext_longoutput):
        if not isinstance(ext_longoutput, list):
            raise TypeError("longoutput is not a list !")
        else:
            self.longoutput = ext_longoutput

    def _add_raw_value(self, ext_raw_value):
        if not isinstance(ext_raw_value, dict):
            raise TypeError("raw_value is not a dict !")
        else:
            self._raw_value = ext_raw_value

    # Internals
    def __getitem__(self, item):
        try:
            return self._raw_value[item]
        except KeyError:
            raise RawValueNameError(item)

    def __iter__(self):
        return self._raw_value.iteritems()