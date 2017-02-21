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

"""Classes for property types."""


class StringProperty(object):
    """Convert powershell string value to python type."""
    @staticmethod
    def pythonize(value):
        """Convert to Python types the ``value``."""
        return unicode(value) if value else unicode('')


class IntegerProperty(object):
    """Convert powershell integer value to python type."""
    @staticmethod
    def pythonize(value):
        """Convert to Python types the ``value``."""
        return int(value)


class BoolProperty(object):
    """Convert powershell boolean value to python type."""
    _bool_mapping = {
        'true': True,
        'false': False
    }

    @staticmethod
    def pythonize(value):
        """Convert to Python types the ``value``."""
        return BoolProperty._bool_mapping[value]
