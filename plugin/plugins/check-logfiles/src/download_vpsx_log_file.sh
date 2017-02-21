#!/bin/bash
#===============================================================================
# Author        : Canux CHENG <canuxcheng@gmail.com>
# Description   : Download VPSX log file for check_logfiles processing.
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

file="/tmp/app_vpsx-active_log_file"
rm -f "$file"
cd /tmp && smbget smb://WWFCSPRN1000.fcs.ww.corp/vpsxlog/active_log_file -p 'NglP(23M,n' -u 9NagiosDC -w CORP -qn -o app_vpsx-active_log_file

