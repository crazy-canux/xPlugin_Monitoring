#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#===============================================================================
# Filename      : notify_by_sms
# Author        : Vincent BESANCON <besancon.vincent@gmail.com>
# Description   : Format a MIME mail and send it to generate a SMS.
#-------------------------------------------------------------------------------
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#===============================================================================

import smtplib
import argparse
from email.mime.text import MIMEText

# Parse arguments
parser = argparse.ArgumentParser(description='Format a MIME mail and send it to generate a SMS.')
parser.add_argument('-m', '--message', required=True, metavar='MESSAGE_BODY', help='The message body that will be in SMS.')
parser.add_argument('-p', '--phone-numbers', required=True, nargs='+', metavar='PHONE_NUMBER@example.com', help='The phone numbers list where to send a SMS, use international format.')

args = parser.parse_args()

# Globals
mail_recipients = []

# Create a text/plain message
msg = MIMEText(args.message)

# Headers
msg['Subject'] = 'Alert'
msg['From'] = "Nagios <nagios@faurecia.com>"
msg['To'] = ';'.join(args.phone_numbers)
msg['CC'] = 'vincent.besancon@faurecia.com'

mail_recipients = args.phone_numbers
mail_recipients.append(msg['CC'])

# Send the message via local sat SMTP server
s = smtplib.SMTP('localhost')
s.sendmail(msg["From"], mail_recipients, msg.as_string())
s.quit()
