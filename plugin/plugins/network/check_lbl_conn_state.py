#!/usr/bin/env python
#-*- coding: UTF-8 -*-
#
# Nagios Plugin
# -------------
#
# Plugin: check_lbl_conn_state.py
# Description: check if the LoadBalancer is receiving connection
#
# Author: Vincent BESANCON <vincent.besancon@faurecia.com>
# SVN: $Id: check_lbl_conn_state.py 139 2009-10-08 14:37:28Z vincent $
#

import os, sys, optparse, subprocess

#-------------------------------------------------------------------------------
## START OF CONFIGURATION ######################################################

# Commands location
snmpwalk='/usr/bin/snmpwalk'

# Default command argument
snmpwalk_opts = "-c %s -v%s -OvQ -m ALL %s 1.3.6.1.4.1.8225.4711.17.1.18"

######################################################## END OF CONFIGURATION ##
#-------------------------------------------------------------------------------

###################
####  Globals  ####
###################

# Nagios
nagios_state = "OK"
nagios_output = ""
nagios_exit_code = 0

# Default SNMP version to use
snmp_version = '1'

#############################
####  Utility functions  ####
#############################

# Show debug message if debug is on
def debug(message):
	if opt.debug:
		sys.stderr.write(message)

#############################
####  Arguments parsing  ####
#############################

progname = os.path.basename(sys.argv[0])

p = optparse.OptionParser()

p.add_option("-H", action="store", dest="hostname", help="The LoadBalancer to probe")
p.add_option("-C", action="store", dest="community", help="The SNMP community to use (default 'public' if not set)")
p.add_option("-2", action="store_true", dest="version", help="Use SNMP version 2c (default 'v1' if not set)")
p.add_option("-d", "--debug", action="store_true", dest="debug", help="Show debug information, Nagios may truncate output")
p.add_option("-i", "--invert", action="store_true", dest="invert", help="Invert status, WARNING becomes OK")

# Set defaults value for args
p.set_defaults(
	community='public',
	version=False,
	debug=False,
	invert=False
)

# Parse arguments on command line
opt, args = p.parse_args()

#########################
####  Sanity checks  ####
#########################

# Check if user entered at least one argument
if len(sys.argv) == 1:
	print "You must at least provide one argument, try '%s --help'" % progname
	sys.exit(3)

# Set SNMP version to use (v1 by default)
if opt.version:
	snmp_version = '2c'

###############################
####  Commands processing  ####
###############################

# Prepare command argument with the ones provided by user
# No str.format() method for python 2.5 :-((
snmpwalk_opts = snmpwalk_opts % (opt.community, snmp_version, opt.hostname)
command = '%s %s' % (snmpwalk, snmpwalk_opts)

debug("Debug is on.\n")
debug("Command being executed: %s\n" % command)
proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out = proc.stdout
err = proc.stderr.read()

# Check if there was any error
if len(err) > 0:
	sys.stderr.write(err)
	sys.exit(3)

debug("Getting output... (please wait):\n")
value = 0
for line in out:
	value += int(line)

debug("Value: " + str(value) + '\n')

if value == 0:
	if opt.invert:
		nagios_state = "OK"
		nagios_exit_code = 0
	else:
		nagios_state = "WARNING"
		nagios_exit_code = 1
	nagios_output = "%s - LoadBalancer does not receive any connections\n" % nagios_state
else:
	if opt.invert:
		nagios_state = "WARNING"
		nagios_exit_code = 1
	else:
		nagios_state = "OK"
		nagios_exit_code = 0
	nagios_output = "%s - LoadBalancer is receiving connections\n" % nagios_state

sys.stdout.write(nagios_output)
sys.exit(nagios_exit_code)