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
This module contains class definition to handle JSON output.
"""

import json

from generic.parser.base import BaseParser
from generic.parser.json.exceptions import InvalidJSONData


class JSONParser(BaseParser):
    """
    A new JSON parser.
    """
    def __init__(self, json_data):
        super(JSONParser, self).__init__()

        # Import external data
        try:
            self._json_data = json_data
            self._external_data = json.loads(self._json_data)
        except ValueError as e:
            raise InvalidJSONData(e)

        # Validate found longoutput and raw values to the parser
        self._add_longoutput(self._external_data["longoutput"])
        self._add_raw_value(self._external_data["raw_value"])