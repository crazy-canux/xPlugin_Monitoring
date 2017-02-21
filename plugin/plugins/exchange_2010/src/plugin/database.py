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

"""Class definition for Database plugins."""

import logging

from .base import PluginBase
from powershell.xml.serialization import XMLSerializedObject

logger = logging.getLogger('plugin.database')


class Database(object):
    """
    Class that represents an Exchange database.

    :param db: the XML serialized object that represents the database.
    :type db: XMLSerializedObject
    """
    def __init__(self, db):
        if not isinstance(db, XMLSerializedObject):
            raise TypeError('Not an instance of XMLSerializedObject !')

        self.name = db['DatabaseName']
        self.status = db['Status']
        self.queue_length = {
            'copy': db['CopyQueueLength'],
            'replay': db['ReplayQueueLength'],
        }
        self.is_primary = False

    def __repr__(self):
        return '{classname} <{dbname}: {dbstatus}, ' \
               'is_primary: {dbtype}, ' \
               'Queues: {queues}>'.format(classname=self.__class__.__name__,
                                          dbname=self.name,
                                          dbstatus=self.status,
                                          dbtype=self.is_primary,
                                          queues=self.queue_length)


class PluginXMLDatabase(PluginBase):
    """Plugin base class for all Database related plugin."""
    def __init__(self, *args, **kwargs):
        super(PluginXMLDatabase, self).__init__(*args, **kwargs)
        xml = self.fetch_xml_table()
        self.databases = [obj
                          for obj in xml
                          if u'DatabaseCopyStatusEntry' in obj.name]


class PluginXMLDatabaseMount(PluginXMLDatabase):
    """Plugin class for Database mount point checks plugin."""
    def main(self):
        """
        Main plugin entry point.

        Implement here all the code that the plugin must do.
        """
        for db in self.databases:
            database = Database(db)

            # Check if this is a primary database and if it should be
            # mounted on the checked host.
            if database.name in self.options.primary_databases:
                if u'Mounted' not in database.status:
                    database.is_primary = True
                    self.add_warning_result(database)
            else:
                if u'Healthy' not in database.status \
                        and not database.name.startswith(u'RecoveryDB_'):
                    self.add_warning_result(database)

        # Exit
        self._prepare_output(problem_pattern='{num} databases are not at their '
                                             'places on this host !',
                             ok_pattern='All databases are correctly mounted '
                                        'on this host.')
        if self.have_criticals or self.have_warnings:
            self.critical(self.output())
        else:
            self.ok(self.output())

    def _prepare_output(self, problem_pattern, ok_pattern):
        """Prepare the message output shown in Nagios."""
        shortoutput = []
        longoutput_pattern = '{name} ({db_type}): {status} ' \
                             '(should be {location})'

        if self.have_criticals or self.have_warnings:
            for severity in self._alerts:
                num_alerts = len(self._alerts[severity])
                if num_alerts:
                    shortoutput.append(problem_pattern.format(num=num_alerts))
                    for result in self._alerts[severity]:
                        details = longoutput_pattern.format(
                            name=result.name,
                            db_type='Primary' if result.is_primary
                                    else 'Replica',
                            status=result.status,
                            location='Mounted' if result.is_primary
                                     else 'Healthy')
                        self.longoutput.append(details)
                self.shortoutput = ', '.join(shortoutput)
        else:
            self.shortoutput = ok_pattern

    def define_plugin_arguments(self):
        """Extra plugin arguments."""
        super(PluginXMLDatabaseMount, self).define_plugin_arguments()
        self.required_args.add_argument(
            '--primary-databases',
            dest='primary_databases',
            nargs='+',
            help='List of primary databases that should be mounted on this '
                 'host.',
            required=True)


class PluginXMLDatabaseQueue(PluginXMLDatabase):
    """Plugin class for Database queue checks plugin."""
    def main(self):
        """
        Main plugin entry point.

        Implement here all the code that the plugin must do.
        """
        for db in self.databases:
            database = Database(db)
            logger.debug(database)
            queue_length = database.queue_length.get(self.options.queue)
            if queue_length >= self.options.critical:
                self.add_critical_result(database)
            elif queue_length >= self.options.warning:
                self.add_warning_result(database)

            # Perfdata
            self.perfdata.append(
                '\'{datasource}_{queue}\'={value};{warn};{crit};0;'.format(
                    datasource=database.name,
                    queue=self.options.queue,
                    value=queue_length,
                    warn=self.options.warning,
                    crit=self.options.critical))

        # Exit
        self._prepare_output(problem_pattern='{num} {queue} queues length '
                                             'more than {thr} !',
                             ok_pattern='All database {queue} queues are '
                                        'normal.')
        if self.have_criticals:
            self.critical(self.output())
        elif self.have_warnings:
            self.warning(self.output())
        else:
            self.ok(self.output())

    def _prepare_output(self, problem_pattern, ok_pattern):
        """Prepare the message output shown in Nagios."""
        shortoutput = []
        longoutput_pattern = '{name} ({queue}): {length}'

        if self.have_criticals or self.have_warnings:
            for severity in sorted(self._alerts.keys()):
                num_alerts = len(self._alerts[severity])
                if num_alerts:
                    shortoutput.append(problem_pattern.format(
                        num=num_alerts,
                        queue=self.options.queue,
                        thr=getattr(self.options, severity)))
                    self.longoutput.append('====== {} ======'.format(
                        severity.upper()))
                    for result in self._alerts[severity]:
                        details = longoutput_pattern.format(
                            name=result.name,
                            queue=self.options.queue,
                            length=result.queue_length[self.options.queue])
                        self.longoutput.append(details)
                self.shortoutput = ', '.join(shortoutput)
        else:
            self.shortoutput = ok_pattern.format(queue=self.options.queue)

    def define_plugin_arguments(self):
        """Extra plugin arguments."""
        super(PluginXMLDatabaseQueue, self).define_plugin_arguments()
        self.required_args.add_argument(
            '--queue',
            dest='queue',
            choices=['copy', 'replay'],
            help='Type of the queue that must be checked.',
            required=True)

        self.required_args.add_argument(
            '-w',
            dest='warning',
            type=int,
            help='Max queue length before warning.',
            required=True)

        self.required_args.add_argument(
            '-c',
            dest='critical',
            type=int,
            help='Max queue length before critical.',
            required=True)

    def verify_plugin_arguments(self):
        super(PluginXMLDatabaseQueue, self).verify_plugin_arguments()
        if self.options.warning > self.options.critical:
            self.unknown('Warning threshold must be < critical !')


class PluginXMLDatabaseMountPBF(PluginBase):
    """Plugin class for Database mount point checks plugin."""
    def main(self):
        """
        Main plugin entry point.

        Implement here all the code that the plugin must do.
        """
        xml = self.fetch_xml_table()

        for database in xml:
            if u'True' not in database['Mounted']:
                self.add_critical_result(database)

        # Exit
        self._prepare_output(problem_pattern='{num} databases are not at their '
                                             'places on this host !',
                             ok_pattern='All databases are correctly mounted '
                                        'on this host.')
        if self.have_criticals or self.have_warnings:
            self.critical(self.output())
        else:
            self.ok(self.output())

    def _prepare_output(self, problem_pattern, ok_pattern):
        """Prepare the message output shown in Nagios."""
        shortoutput = []
        longoutput_pattern = '{Name}: not mounted !'

        if self.have_criticals or self.have_warnings:
            for severity in self._alerts:
                num_alerts = len(self._alerts[severity])
                if num_alerts:
                    shortoutput.append(problem_pattern.format(num=num_alerts))
                    for result in self._alerts[severity]:
                        details = longoutput_pattern.format(**result)
                        self.longoutput.append(details)
                self.shortoutput = ', '.join(shortoutput)
        else:
            self.shortoutput = ok_pattern
