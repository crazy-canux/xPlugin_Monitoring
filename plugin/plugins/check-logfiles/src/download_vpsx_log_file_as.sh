#!/bin/bash
#===============================================================================
# Author        : Yves ANDOLFATTO <yves.andolfatto@Company.com>
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

file="/tmp/app_vpsx-active_log_file_as"
rm -f "$file"
cd /tmp && smbget smb://WWFCSAPP0201.fcs.toa.prim/LRSROOT$/vpsxroot/log/active_log_file -p 'NglP(23M,n' -u 9NagiosDC -w TOA -qn -o app_vpsx-active_log_file_as

