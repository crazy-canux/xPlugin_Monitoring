================================================================================
:mod:`jit.interface` -- XML interface module
================================================================================

.. module:: jit.interface

This module contains both classes to define plugins that make use of the `XML
interface`_ and the :class:`XMLInterface` class responsible to handle the XML
interface.

.. autoclass:: XMLInterface
    :members:

Get event for a type
====================

::

 >>> xml = XMLInterface(xml_data)
 >>> xml['Event']

It returns an :class:`Event` object containing
the data about the selected event type.

The :class:`Event` object
=========================

The :class:`Event` class is used to store data for one event (support multi tags
for one event).

.. autoclass:: Event
    :members:

.. links:

.. _XML interface: http://canuxcheng.com/tracking/projects/gimm/wiki/#XML-interface-specification
