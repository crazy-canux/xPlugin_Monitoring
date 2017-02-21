# -*- coding: utf-8 -*-
#===============================================================================
# Copyright (c) Canux CHENG <canuxcheng@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#===============================================================================

"""
This module contains the plugin class definition.
"""

import argparse
import requests

from pdm.exceptions import PDMHttpError, PDMLoginFailed


class PDMLogin(object):
    """
    The Nagios plugin to verify PDM login on a specified node of the cluster.

    :param description: the description shown with --help arg.
    :type description: basestring
    :param arguments: used for tests, specify arguments without command
                      line.
    :type arguments: list
    """
    HOME_URL = "{base_url}/emxLogin.jsp"
    LOGIN_SERVLET = "{base_url}/servlet/login"
    LOGOUT = "{base_url}/emxLogout.jsp"

    def __init__(self, description="", version="", arguments=None):
        # Parse command line arguments
        self._parse_arguments(description, version, arguments)

        # HTTP request session object
        self.session = requests.Session()

        # PDM URLs
        self.home_url = PDMLogin.HOME_URL.format(
            base_url=self.args.url)
        self.login_servlet = PDMLogin.LOGIN_SERVLET.format(
            base_url=self.args.url)
        self.logout_url = PDMLogin.LOGOUT.format(
            base_url=self.args.url)

    def _parse_arguments(self, desc, version, args):
        """
        Define and parse the command line arguments. Ensure they are valid.
        """
        self.parser = argparse.ArgumentParser(description=desc,
                                              version=version)

        plugin_args = self.parser.add_argument_group(
            "Plugin arguments",
            "List of all available plugin arguments")

        plugin_args.add_argument("-u", "--url",
                                 required=True,
                                 help="PDM base URL like "
                                      "http://numgen.app.corp:11105/prod_ng.")
        plugin_args.add_argument("-c", "--cloneid",
                                 required=True,
                                 help="The node cloneID like 17cu31omc.")
        plugin_args.add_argument("-l", "--login",
                                 required=True,
                                 help="Username to use for login.")
        plugin_args.add_argument("-p", "--password",
                                 required=True,
                                 help="Username password to use for login.")

        self.args = self.parser.parse_args(args)

        # Strip URL
        self.args.url = self.args.url.strip("/")

    @property
    def jsession_token(self):
        """
        Property that returns the JSESSION token (before the cloneID) from
        JSESSIONID cookie::

         JSESSIONID=[TOKEN]:cloneID

        :returns: the TOKEN string of the cookie.
        :raises: :class:`pdm.exceptions.PDMHttpError`
        """
        try:
            home_request = self.session.get(self.home_url)
            home_request.raise_for_status()
        except requests.RequestException as e:
            raise PDMHttpError("Unable to access PDM home url: %s\n"
                               "URL: %s" % (e, self.home_url))

        token = home_request.cookies["JSESSIONID"].split(":")[0]

        return token

    def _create_jsession_cookie(self):
        """
        Creates the JSESSIONID cookie in order to establish a login on the
        specified clone id.
        """
        return {"JSESSIONID": "{}:{}".format(self.jsession_token,
                                             self.args.cloneid)}

    def login(self):
        """
        Establish a POST request to the login servlet sending as POST data
        the login and password specified from command line.

        :raises: :class:`pdm.exceptions.PDMHttpError`,
                 :class:`pdm.exceptions.PDMLoginFailed`
        """
        credentials = {
            'login_name': self.args.login,
            'login_password': self.args.password
        }

        try:
            login_request = self.session.post(
                self.login_servlet,
                data=credentials,
                cookies=self._create_jsession_cookie())
            login_request.raise_for_status()
        except requests.RequestException as e:
            raise PDMHttpError("Unable to send login information: %s\n"
                               "URL: %s" % (e, self.logout_url))

        # Check that we had a successful auth with the login and password
        if not login_request.url.endswith("emxNavigator.jsp"):
            raise PDMLoginFailed(
                "Unable to login with user '%s' !" % self.args.login)

    def logout(self):
        """
        Close the session properly.
        """
        self.session.get(self.logout_url)