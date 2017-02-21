#!/usr/bin/env python2.7
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
msg['From'] = "Nagios <nagios.com>"
msg['To'] = ';'.join(args.phone_numbers)
msg['CC'] = 'canuxcheng@gmail.com'

mail_recipients = args.phone_numbers
mail_recipients.append(msg['CC'])

# Send the message via local sat SMTP server
s = smtplib.SMTP('localhost')
s.sendmail(msg["From"], mail_recipients, msg.as_string())
s.quit()
