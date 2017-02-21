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

"""Module to represents a Powershell XML serialized objects."""

import logging
import re

from bs4 import Tag

from .base import BaseXML
from .exceptions import XMLValidityError
from ..properties import IntegerProperty, StringProperty, BoolProperty

logger = logging.getLogger('plugin.replication')


class XMLSerializedObject(object):
    """
    Represents a serialized object entry from the XML "obj" tag.

    :param obj_tag: the XML tag "obj" entry.
    :type obj_tag: bs4.element.Tag
    """
    _types_mapping = {
        'i32': IntegerProperty,
        'i64': IntegerProperty,
        'b': BoolProperty,
        's': StringProperty,
    }

    def __init__(self, obj_tag=None):
        if isinstance(obj_tag, Tag):
            try:
                self._tag = obj_tag
                self.refid = int(self._tag['refid'])
                self.name = self._tag.tostring.string.split('/')[-1]
                print self.name
                self.properties = self._pythonize_properties()
            except (KeyError, ValueError, AttributeError) as exc:
                raise XMLValidityError('Not a valid serialized object !',
                                       exc.message)
        else:
            raise TypeError('Not a BeautifulSoup Tag instance !')

    def _pythonize_properties(self):
        """Pythonize property tags to a dict."""
        props = {}
        types_mapping = XMLSerializedObject._types_mapping

        for prop in self._tag.props.contents:
            if isinstance(prop, Tag):
                prop_name = prop['n']
                if u'obj' in prop.name and prop.tostring:
                    if prop.name in types_mapping:
                        conv = types_mapping.get(prop.name)
                        prop_value = conv.pythonize(prop.tostring.string)
                    else:
                        prop_value = prop.tostring.string
                else:
                    if prop.name in types_mapping:
                        conv = types_mapping.get(prop.name)
                        prop_value = conv.pythonize(prop.string)
                    else:
                        prop_value = prop.string
                props.update({prop_name: prop_value})
        return props

    def has_property(self, name):
        """Check that the serialized object has property ``name``."""
        return name in self

    def get(self, *args, **kwargs):
        """Wrapper to dict.get()."""
        return self.properties.get(*args, **kwargs)

    def keys(self):
        """Wrapper to dict.keys()."""
        return self.properties.keys()

    def __getitem__(self, prop):
        return self.properties.__getitem__(prop)

    def __iter__(self):
        return self.properties.__iter__()

    def __repr__(self):
        """Object representation as text."""
        return '{0} <{1}, Tag={2}, RefID={3}>'.format(self.__class__.__name__,
                                                      self.name,
                                                      self._tag.name,
                                                      self.refid)


class XMLSerializedTable(BaseXML):
    """
    Represents as a table the XML serialized objects from Powershell XML
    export cmdlet.

    :param xml: XML file handle or string.
    :type xml: str, unicode, file
    """
    def __init__(self, xml):
        super(XMLSerializedTable, self).__init__(xml)
        self.root = self.xml.objs

        try:
            self._tag_objects = self.root.find_all(
                XMLSerializedTable._tag_is_serialized_object)
            self._objects = self._pythonize_objects()
        except (AttributeError, RuntimeError):
            raise XMLValidityError('No serialized object found !')

    def _pythonize_objects(self):
        """Pythonnize all objects found and returns the list."""
        objs = []
        for obj in self._tag_objects:
            objs.append(XMLSerializedObject(obj))
        if objs:
            return objs
        else:
            raise RuntimeError('No serialized object found !')

    @staticmethod
    def _tag_is_serialized_object(tag):
        """Detect if ``tag`` is a serialized powershell object."""
        if u'obj' in tag.name and tag.attrs.keys() == ['refid']:
            if u'objs' not in tag.parent.name:
                if u'Microsoft.PowerShell.Commands.Internal.Format.' \
                        not in tag.tostring.string:
                    return True
        return False

    def match(self, property_name, regex, object_name=None, invert=False):
        """
        Match for ``regex`` in ``property_name`` value. The match can be
        inverted setting ``invert`` to true, useful to where a test has failed::

            # Returns all objects where property ``Result`` is not a success.
            match('Result', r'^Success$', invert=True)

        :returns: a list of serialized objects.
        """
        try:
            pattern = re.compile(regex)
        except re.error:
            raise

        logger.debug('Searching for property "%s" with value matching "%s"...',
                     property_name,
                     regex)
        if object_name:
            logger.debug('Filtering on object name: %s', object_name)

        matches = []
        for obj in self:
            if property_name in obj:
                logger.debug('Property "%s" is found in object "%s" with id '
                             '"%d". Value is "%s".',
                             property_name,
                             obj.name,
                             obj.refid,
                             obj.get(property_name))
                if object_name:
                    if object_name in obj.name:
                        if pattern.match(obj.get(property_name)):
                            if not invert:
                                matches.append(obj)
                        else:
                            if invert:
                                matches.append(obj)
                else:
                    if pattern.match(obj.get(property_name)):
                        if not invert:
                            matches.append(obj)
                    else:
                        if invert:
                            matches.append(obj)
        return matches

    def list_object_names(self):
        """Returns the distinct name of all objects."""
        return {obj.name for obj in self}

    def get(self, refid):
        """Returns the object entry with id attribute ``refid``."""
        for obj in self:
            if obj.refid == refid:
                return obj

    def __getitem__(self, obj):
        return self._objects.__getitem__(obj)

    def __iter__(self):
        return self._objects.__iter__()

    def __repr__(self):
        """Object representation as text."""
        return repr(self._objects)
