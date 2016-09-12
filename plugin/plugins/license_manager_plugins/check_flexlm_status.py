#!/usr/bin/env python2.7
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

# Python Std Lib
import re
import backend.flexlm
import backend.util
from nagios.errorlevels import NagiosCritical, NagiosOk
from nagios.arguments import process_plugin_options


def format_perfdata(features):
    """Format the output of performance data"""
    perfdata = " | "
    for feature in features:
        if feature["status"] == "OK":
            perfdata += "'%s'=%s;;;0;%s " % (feature["name"], feature["in_use"], feature["total"])
    
    return perfdata.rstrip()


def run():
    """Execute the plugin"""
    # Plugin arguments
    options = process_plugin_options()
    
    # Get the output of lmutil / lmstat, catching errors
    try:
        if options.debug:
            output = backend.util.test_from_file("../tests/lmstat_status.txt")
        else:
            output = backend.flexlm.status("%s" % options.license,
                                           options.timeout,
                                           options.with_stat)
    except backend.flexlm.FlexlmStatusError as e:
        raise NagiosCritical("%s (code: %s, license: '%s') !" % (e.errmsg, e.retcode, e.license))
    
    # Some globals
    all_feature_stats = []             # Store all features statistics
    feature_error = 0                  # Counter for the number of feature in error
    total_license_available = 0        # The total license available (sum of total license issued for all features)
    total_license_used = 0             # The total license in use (sum of total license in use for all features)
    vendor_daemon = ""                 # Store the vendor daemon name
    
    # Compile regexp used to check output
    regexp_vendor_daemon = re.compile(r'\s*(.*): UP')
    regexp_feature_name = re.compile(r'^Users of (.*):')
    regexp_feature_stats = re.compile(r'^Users of .*: .* of (?P<total>\d+) .* issued; .* of (?P<in_use>\d+) .* in use')

    # Checking if Vendor daemon is UP
    for line in output:
        match = regexp_vendor_daemon.search(line)
        if match:
            vendor_daemon = match.group(1)
    
    if len(vendor_daemon) == 0:
        raise NagiosCritical("No vendor daemon is running !")

    if options.with_stat:
        # Retrieve features informations
        for line in output:
            feature = {
                       'name': '',
                       'in_use': '0',
                       'total': '0',
                       'status': '',
            }
            match_feature_line = regexp_feature_name.search(line)
            if match_feature_line:
                # Store feature name
                feature["name"] = match_feature_line.group(1)

                # Checking if this is possible to get stats from the feature
                match_feature_stats = regexp_feature_stats.search(line)
                if match_feature_stats:
                    feature.update(match_feature_stats.groupdict())
                    feature["status"] = "OK"

                    # Calculate some stats about license usage
                    total_license_available += int(feature["total"])
                    total_license_used += int(feature["in_use"])
                else:
                    feature["status"] = "ERROR"
                    feature_error+=1

                all_feature_stats.append(feature)

        # Formating Nagios output
        #
        nagios_output = ""
        nagios_longoutput = ""
        nagios_perfdata = format_perfdata(all_feature_stats)

        # Output if errors are found in features
        if feature_error > 0:
            if not options.nolongoutput:
                for feature in all_feature_stats:
                    if feature["status"] == "ERROR":
                        nagios_longoutput += "Feature: %s\n" % feature["name"]

            nagios_output = "%s: %d feature(s) in error(s) !\n%s" % (vendor_daemon, feature_error, nagios_longoutput.rstrip('\n'))
            raise NagiosCritical(nagios_output + nagios_perfdata)

        # Output when everything is fine
        #
        if not options.nolongoutput:
            for feature in all_feature_stats:
                nagios_longoutput += "Feature '%s': %s / %s\n" % (feature["name"], feature["in_use"], feature["total"])

        nagios_output = "%s: usage: %d / %d license(s) available.\n%s" % (vendor_daemon, total_license_used, total_license_available, nagios_longoutput.rstrip('\n'))

        raise NagiosOk(nagios_output + nagios_perfdata)
    else:
        raise NagiosOk("Vendor daemon %s is up !" % vendor_daemon)
    
# Main
if __name__ == "__main__":
    run()
