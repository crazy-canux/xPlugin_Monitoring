================================================================================
:mod:`jit.plugin` -- Creating plugins
================================================================================

.. module:: jit.plugin

The module :mod:`jit.plugin` provides easy classes to create new plugins.

The Base class
==============

There is a base class that you may want to inherit from in order to initialize a
new Nagios plugin that interact with the XML interface.

.. autoclass:: XMLInterfacePlugin

A default set of new command line arguments are made available using this class:

.. attribute:: XMLInterfacePlugin.options.url

    :command line: ``--url``

    URL location of the XML interface. Can be over http:// or ftp://.

Helper class
============

An helper class to create new plugin checking specific events is also available.

.. autoclass:: XMLEventPlugin

.. attribute:: XMLEventPlugin.options.event

    :command line: ``-e`` or ``--event``

    gIMM event to check.
