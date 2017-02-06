#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse

repo_list = [
    'plugins/e-supply.git',
    'plugins/mssql.git',
    'plugins/generic.git',
    'plugins/notify.git',
    'plugins/check-objectstore.git',
    'plugins/windows.git',
    'plugins/system.git',
    'plugins/exchange_2010.git',
    'plugins/sharepoint_2013.git',
    'plugins/check-logfiles.git',
    'plugins/vmware.git',
    'plugins/check_wmi_plus.git',
    'plugins/db2.git',
    'plugins/ad2012.git',
    'plugins/license_manager_plugins.git',
    'plugins/oracle.git',
    'plugins/mosaic.git',
    'plugins/ebcs.git',
    'plugins/colisee-clients.git',
    'plugins/storage.git',
    'plugins/ldap.git',
    'plugins/nrft.git',
    'plugins/elasticsearch.git',
    'plugins/pdm.git',
    'plugins/omnibus.git',
    'plugins/network.git',
    'plugins/nemo.git',
    'plugins/mysql.git',
    'plugins/misc-app.git',
    'plugins/jit.git',
    'plugins/hadr.git',
    'plugins/hacmp.git',
    'plugins/exalead.git',
    'plugins/erp-archiving.git',
    'plugins/check-multi.git',
    'plugins/check-file-existence.git',
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='git clone repo')
    parser.add_argument('-d', '--dest',
                        default='/home/chengca/myCode/zplugin/plugin/plugins/',
                        required=False,
                        help='default is %(default)s',
                        dest='dest')
    args = parser.parse_args()

    for repo in repo_list:
        cmd = "cd %s;git clone git@monitoring-dc.app.corp:%s" % (args.dest, repo)
        print cmd
        os.system(cmd)
