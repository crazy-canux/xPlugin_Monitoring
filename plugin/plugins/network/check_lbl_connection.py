#!/usr/bin/env python

###############################################################################
#
# check_lbl_connection.py: check connection active and inactive for all
#                         application
#
# Usage: check_lbl_connection.py [-h] [--debug] [--version] -H HOSTNAME
#                               [-f file_app]
#
# Create: 21/06/2013
# Author: BAILAT Patrick
#
# Modify: JJ/MM/AAAA
# Author:
# Object:
#
###############################################################################

import logging
from monitoring.nagios.plugin import NagiosPluginSSH

logger = logging.getLogger('plugin.network.lbl')


class PluginLbl(NagiosPluginSSH):
    def define_plugin_arguments(self):
        super(PluginLbl, self).define_plugin_arguments()

        self.required_args.add_argument('-f', '--fileapp',
                                        dest="file_app",
                                        help="File of application, an string",
                                        required=False)

# Init plugin
plugin = PluginLbl(version=1.0,
                   description="check connection active and inactive on lbl")


# Final status exit for the plugin
status = None

cmd = "sudo /sbin/ipvsadm -L -n | sed '1,3d'"
logger.debug("cmd : {0}".format(cmd))

command = plugin.ssh.execute(cmd)
output = command.output
errors = command.errors

if errors:
    plugin.unknown("Errors found:\n{}".format("\n".join(errors)))

# recuperation file
if plugin.options.file_app:
    cmd_file = "cat {0}".format(plugin.options.file_app)
    logger.debug("cmd_file : {0}".format(cmd_file))

    command_file = plugin.ssh.execute(cmd_file)
    output_file = command_file.output
    errors_file = command_file.errors
    logger.debug("output_file : {0}".format(output_file))

    if errors_file:
        plugin.unknown("Errors found:\n{}".format("\n".join(errors_file)))
else:
   output_file = None

# Travel output cmd by line
cmpt = 0
f_virt = 0
total_active = 0
total_inactive = 0
result = {}
app_name = "App"

for line in output:
    logger.debug(line)
    status = plugin.ok
    # server virtuel
    if "TCP" in line:
        cmpt += 1
        f_virt = 0
        server = {}
        v_ip = line.split()[1]
        logger.debug("v_ip " + v_ip )
        if output_file is not None:
            # recherche de l'ip dans le fichier des application a checker
            for line_file in output_file:
                app_name, app_ip = line_file.split()
                if v_ip == app_ip:
                    f_virt = 0
                    break
                else:
                    # ip non presente
                    f_virt = 1
        logger.debug("name " + app_name)

    # serveur reel
    else:
        # on ignore les serveur reel pour les application non souhaite
        if f_virt != 0:
            continue

        other, r_ip,  forward, weight, act_conn, inact_conn = line.split()
        act_conn = int(act_conn)
        inact_conn = int(inact_conn)
        if r_ip == "127.0.0.1:.*":
            act_conn = 0
            inact_conn = 0

        # Total Active et inactive
        total_active += act_conn
        total_inactive += inact_conn

        server[r_ip] = {'actconn': act_conn, 'inactconn': inact_conn}

        if v_ip in result:
            if 'actconn' in result[v_ip]:
                act_conn += result[v_ip]['actconn']
            if 'inactconn' in result[v_ip]:
                inact_conn += result[v_ip]['inactconn']

        result[v_ip] = {'name': app_name,
                        'actconn': act_conn,
                        'inactconn': inact_conn,
                        'server': server}


plugin.shortoutput = "Total Connection on LBL: {} Active,  \
                     {} Inactive".format(total_active, total_inactive)
logger.debug(result)

# Affichage du dico result
for virt_ip in result.keys():
    logger.debug("virtuel " + virt_ip)

    plugin.longoutput.append("{} ({}): {} Active,  {} Inactive".format(result[virt_ip]['name'],
                                                                       virt_ip,
                                                                       result[virt_ip]['actconn'],
                                                                       result[virt_ip]['inactconn']))
    plugin.perfdata.append('{table}={value};;;0'.format(table="active_" +  result[virt_ip]['name'] + "_" + virt_ip,
                                                        value= result[virt_ip]['actconn']))
    plugin.perfdata.append('{table}={value};;;0'.format(table="inactive_" +  result[virt_ip]['name'] + "_" + virt_ip,
                                                        value= result[virt_ip]['inactconn']))
    dico_vip = result[virt_ip]['server']
    for real_ip in dico_vip.keys():
        logger.debug("server "+ real_ip)
        plugin.longoutput.append(" -> {}: {} Active,  {} Inactive".format(real_ip,
                                                                          dico_vip[real_ip]['actconn'],
                                                                          dico_vip[real_ip]['inactconn']))
        plugin.perfdata.append('{table}={value};;;0'.format(table="active_" + result[virt_ip]['name'] + "_realserver_" + real_ip,
                                                            value=dico_vip[real_ip]['actconn']))
        plugin.perfdata.append('{table}={value};;;0'.format(table="inactive_" +  result[virt_ip]['name'] + "_realserver_" + real_ip,
                                                            value=dico_vip[real_ip]['inactconn']))

# Return status with message to Nagios
logger.debug("Return status and exit to Nagios.")
if status:
    status(plugin.output(long_output_limit=None))
else:
    plugin.unknown('Unexpected error during plugin execution, please investigate with debug mode on.')
