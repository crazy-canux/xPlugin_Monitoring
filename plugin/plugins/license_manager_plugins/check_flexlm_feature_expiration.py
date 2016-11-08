#!/usr/bin/env python2.7
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

# TODO: Add thresholds defined by arguments

import re
from datetime import datetime
import backend.flexlm
import backend.util
from nagios.errorlevels import NagiosCritical, NagiosWarning, NagiosOk
from nagios.arguments import process_plugin_options

def time_left(expire_date):
    """Return remaining days before feature expiration or 0 if expired."""
    today_dt = datetime.today()
    expire_dt = datetime.strptime(expire_date, "%d-%b-%Y")
    
    # Calculate remaining days before expiration
    days_left_td = expire_dt - today_dt
    days_left = days_left_td.days
    if days_left <= 0:
        days_left = 0
        
    return days_left

def run():
    """Execute the plugin"""
    # Plugin arguments
    options = process_plugin_options()
    
    # Get the output of lmutil / lmstat, catching errors
    try:
        if options.debug:
            output = backend.util.test_from_file("../tests/lmstat_expiration.txt")
        else:
            output = backend.flexlm.expiration("%s" % options.license, options.timeout)
    except backend.flexlm.FlexlmStatusError as e:
        raise NagiosCritical("%s (code: %s, license: '%s') !" % (e.errmsg, e.retcode, e.license))
    
    # Some globals
    features_list = {
        'uptodate': [],
        'about_to_expire': [],
        'expired': [],
    }                                       # Store all features informations.
    nbfeature_expired = 0                   # Counter for the number of expired.
                                            # feature.
    nbfeature_about_to_expire = 0           # Counter for the number of feature
                                            # about to expire.
    
    # Compile regexp used to check lmstat output
    regexp_feature_info = re.compile(
        r'^(?P<name>\w*).*(?P<expire_date>\d{2}-.{3}-\d{4})')
    
    # Retrieve features informations
    for line in output:
        # The feature dict contains the following keys: name, expire_date.
        # name: the feature name as string.
        # expire_date: the date string of the form "%d-%b-%Y" when this feature
        # will expire.
        feature = {}
        match_feature_info_line = regexp_feature_info.search(line)
        if match_feature_info_line:
            feature.update(match_feature_info_line.groupdict())
            
            remaining_days = time_left(feature['expire_date'])
            if 0 < remaining_days < 15:
                nbfeature_about_to_expire += 1
                features_list['about_to_expire'].append(
                    (feature['name'], feature['expire_date']))
            elif remaining_days <= 0:
                nbfeature_expired += 1
                features_list['expired'].append(feature['name'])
            else:
                features_list['uptodate'].append((feature['name'],
                                                  feature['expire_date']))

    # Formating Nagios output
    #
    nagios_output = ""
    nagios_longoutput = ""

    # Checking if there is feature with problem, then output to Nagios
    if len(features_list['expired']) > 0:
        nagios_output = "There are %d licenses expired !\n" % len(
            features_list['expired'])
        if not options.nolongoutput:
            for feature in features_list['expired']:
                nagios_longoutput += "Feature '%s' is expired !\n" % feature
        raise NagiosCritical(nagios_output + nagios_longoutput)
    elif len(features_list['about_to_expire']) > 0:
        nagios_output = "There are %d licenses about to expire !\n" % len(
            features_list['about_to_expire'])
        if not options.nolongoutput:
            for feature in features_list['about_to_expire']:
                name, expire_date = feature
                nagios_longoutput += "Feature '%s' will expire on %s !\n" % (
                    name, expire_date)
        raise NagiosWarning(nagios_output + nagios_longoutput)
    else:
        nagios_output = "All features licenses are up to date.\n"
        if not options.nolongoutput:
            for feature in features_list['uptodate']:
                name, expire_date = feature
                nagios_longoutput += "Feature '%s' will expire on %s.\n" % (
                    name, expire_date)
        raise NagiosOk(nagios_output + nagios_longoutput)
    
# Main
if __name__ == "__main__":
    run()
