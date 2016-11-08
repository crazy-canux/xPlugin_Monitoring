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
:mod:`jit.interface` module
============================

Contains classes that handle the XML interface file parsing and events
collection.
"""

# Std imports
import logging
from datetime import datetime
from pprint import pformat

# Exceptions
from exceptions import *

# Monitoring imports
from monitoring.nagios.plugin import NagiosPlugin

# 3rd party imports
from bs4 import BeautifulSoup


logger = logging.getLogger('plugin.jit.interface')

SEVERITY_LEVEL = {
    'OK': (0, NagiosPlugin.ok),
    'INFO': (0, NagiosPlugin.ok),
    'WARNING': (1, NagiosPlugin.warning),
    'CRITICAL': (2, NagiosPlugin.critical),
    'UNUSED': (0, NagiosPlugin.ok),
}


class Event(object):
    """
    The :class:`Event` class store information about an event from the XML
    interface. Its function is to collect all tags for an event and store the
    main message that will be redirected to Nagios with the severity and extra
    messages as long output.

    :param events: list of tags for the event from the XML file.
    :type events: list

    The following instance attributes are made available:

    .. attribute:: Event.name

        This is the name of the event in JIT application.

    .. attribute:: Event.severity

        The Nagios severity to return. This is one of the following unbound
        methods:

        - :meth:`NagiosPlugin.ok`
        - :meth:`NagiosPlugin.warning`
        - :meth:`NagiosPlugin.critical`

    .. attribute:: Event.message

        The message used in Nagios short output. The one that will be attached
        to the alert.

    .. attribute:: Event.details

        A list of the lines for long output or any extra details about the
        alert.
    """
    def __init__(self, events):
        self._events = events
        self.name = events[0].string
        self.main = self._find_tag_with_highest_severity()
        self.severity = SEVERITY_LEVEL[self.main.severity.string][1]
        if self.main.message.string != "UNUSED":
            self.message = self.main.message.string
        else:
            self.message = "This check is not verified on this host."
        self.details = []

        # Get extra details messages (for long output)
        for event in self._events:
            parent = event.parent
            self.details.append(parent.message.string)

    def _find_tag_with_highest_severity(self):
        all_tags_severity = []

        for tag in self._events:
            parent = tag.parent
            parent_severity = parent.severity.string
            try:
                all_tags_severity.append(SEVERITY_LEVEL[parent_severity][0])
            except KeyError:
                raise UndefinedSeverity(parent_severity, self.name)

        hightest_severity_tag_index = all_tags_severity.index(
            max(all_tags_severity))
        main = self._events.pop(hightest_severity_tag_index)

        return main.parent

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<class '{0}' Type: {1.name}, " \
               "Severity: {1.severity}, " \
               "Message: {1.message}, " \
               "{2} long output>".format(self.__class__.__name__,
                                         self,
                                         len(self.details))


class XMLInterface(object):
    """
    Class :class:`XMLInterface` interacts with the XML interface defined between
    monitoring and industrialization applications.

    The following instances attributes are made available:

    .. attribute:: XMLInterface.version

        This is the version of the XML file.

    .. attribute:: XMLInterface.role

        Role of the server (``MAIN`` or ``BACKUP``).

    .. attribute:: XMLInterface.last_updated

        The date time of the last update. Used to check if monitoring data is
        up-to-date warn if not.

    .. attribute:: XMLInterface.events

        The attribute that stores all data about found events from the XML file.

    .. attribute:: XMLInterface.xml

        The is the :class:`BeautifulSoup` instance.
        Use it to do what you want with the XML file.

    **Usage**::

     >>> interface = XMLInterface(open('sample_data/interface.xml'))
     >>> event = interface['CheckForecast']
     >>> event.message
     u'Forecast has been NOT integrated correctly in the last 30 Hours'
     >>> event.details
     [u'EdiCounter: 00455 Date: 2012-10-27 02:40:07.857.Processed OK. \
Additions: Number: 72', \
u'EdiCounter: 00455 Date: 2012-10-27 02:40:07.857.Processed OK. \
Deletes: Number: 0', \
u'EdiCounter: 00455 Date: 2012-10-27 02:40:07.857.\
Processed OK. Updates: Number: 209']
     >>> event.severity
     <unbound method NagiosPlugin.warning>
     >>> interface.last_updated
     datetime.datetime(2012, 11, 13, 15, 56, 4)
     >>> interface.version
     u'3.8.0'
     >>> interface.role
     u'MAIN'
    """
    def __init__(self, xml_data):
        """
        Read XML data and collect all related events.

        :param xml_data: a file-object or string which is valid XML.
        :type xml_data: file, basestring
        """
        logger.debug('XML Interface initialization.')

        # Initialize the XML parser
        self.xml = BeautifulSoup(xml_data)

        # Internals
        self.events = []
        self.last_updated = datetime.strptime(
            self.xml.alerts.source.datetime.string, '%d-%m-%Y_%H:%M:%S')
        self.version = self.xml.alerts.source.version.text
        self.role = self.xml.alerts.source.role.text

        # Start collecting the events
        self._collect_events()

    def _collect_events(self):
        """
        Collect all events and store :class:`Event` instances in :attr:`events`
        list.
        """
        # Get the list of available events and deduplicate
        event_types = []
        logger.debug('Available events:')
        for event in self.xml.alerts.events.find_all('event-name'):
            event_name = event.string
            if not event_name in event_types:
                logger.debug('\t%s', event_name)
                event_types.append(event_name)

        # Get all tags for an event
        for event_type in event_types:
            event_tags = self.xml.alerts.events.find_all('event-name',
                                                         text=event_type)
            self.events.append(Event(event_tags))

        logger.debug('Events data:\n%s', pformat(self.events, indent=4))

    def __getitem__(self, eventname):
        """
        Return the :class:`Event` instance for the corresponding event ``name``.
        """
        found_event = None
        for event in self.events:
            if event.name == eventname:
                found_event = event
                break

        if not found_event:
            raise EventNotFound

        return found_event