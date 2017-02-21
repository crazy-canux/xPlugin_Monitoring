.. plugin-app-pdm documentation master file, created by
   sphinx-quickstart on Fri Aug  2 09:28:48 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=================================
``plugin-app-pdm`` specifications
=================================

This is the specifications for **plugin-app-pdm**, the Nagios plugin that
verify if login can be done on a specified node of the cluster.

`Source code`_ is available into a `Git`_ repository.

.. toctree::
    :maxdepth: 2

    reference

Usage
=====

Help is available with argument ``--help``::

 usage: check_pdm_login.py [-h] -u URL -c CLONEID -l LOGIN -p PASSWORD

 Test login to PDM using HTTP on a specified node.

 optional arguments:
   -h, --help            show this help message and exit

 Plugin arguments:
   List of all available plugin arguments
 
   -u URL, --url URL     PDM base URL like
                         http://numgen.app.corp:11105/prod_ng.
   -c CLONEID, --cloneid CLONEID
                         The node cloneID like 17cu31omc.
   -l LOGIN, --login LOGIN
                         Username to use for login.
   -p PASSWORD, --password PASSWORD
                         Username password to use for login.

Tests
=====

Run the tests from project root directory with ``runtests.py``::

 $ runtests.py
 test_bad_cloneid (__main__.PDMLoginTest) ... ok
 test_get_jsession_token (__main__.PDMLoginTest) ... ok
 test_good_cloneid (__main__.PDMLoginTest) ... ok
 test_http_error (__main__.PDMLoginTest) ... ok
 test_set_jsession_cookie (__main__.PDMLoginTest) ... ok
 test_unauthorized_login (__main__.PDMLoginTest) ... ok

 ----------------------------------------------------------------------
 Ran 6 tests in 1.177s

 OK

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Source code: http://canuxcheng.com/tracking/projects/pdm/repository
.. _Git: http://git-scm.com/
