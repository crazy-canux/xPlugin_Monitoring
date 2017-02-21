#!/bin/ksh
################################################################################
#
# check_magnitude_active_session.sh :
#          execution du script usersbybervers_Scor_Prod.cmd par
#          intermediere du script check_nrpe (agent Nagios)
#          et formatage de la sorti du script
#
# Syntaxe: check_magnitude_active_session.sh -H host [-w warn ] [-c critical]
#
# Date creation: 27/09/2011
# Auteur: BAILAT Patrick
#
# Date modification:
# Auteur:
# Objet:
#
################################################################################

typeset -i rc_code=0
status="OK"
ls_cmd="/usr/lib/canux/plugins"

# ===============================> fonctions <================================ #

# usage (): affiche l'usage du script et sort du programme
#
usage ()
{
  usage_str="usage: %s -H host [-w warn] [ -c critical]"

  printf "$usage_str" $prog_name
  exit
}


# =================================> Main <=================================== #

while getopts "w:c:H:" option
do
  case $option in
    w) warn=$OPTARG;;
    c) critical=$OPTARG;;
    H) host=$OPTARG;;
  esac
done

[ -z "$host" ] && usage

# execution du script par check_nrpe
cmd=$($ls_cmd/check_nrpe -H $host -c check_magnitude_active_sessions)
if [ $? -ne 0 ] 
then
  print "UNKNOWN - Invokation of check_nrpe failed"
  exit 3
fi
print "$cmd" | tail -n1 | IFS=';' read t_user m_user w_user e_user b_user

max=$((t_user+1))

# verifie si au dessus d'un seuil 
if [ -n "$warn" ]
then
  max=$((warn+1))
  if [ "$t_user" -ge "$warn" ]
  then
    max=$((t_user+1))
    status="WARNING"
    rc_code=1
  fi
fi

if [ -n "$critical" ]
then
  max=$((critical+1))
  if [ "$t_user" -ge "$critical" ]
  then
    max=$((t_user+1))
    status="CRITICAL"
    rc_code=2
  fi
fi

#Perfdata
perf="| 'Total_users'=${t_user}U;${warn};${critical};0;${max}"
perf="$perf 'Total_Mag_users'=${m_user}U;${warn};${critical};0;${max}"
perf="$perf 'Total_Web_users'=${w_user}U;${warn};${critical};0;${max}"
perf="$perf 'Total_Excel_users'=${e_user}U;${warn};${critical};0;${max}"
perf="$perf 'Total_Batch_users'=${b_user}U;${warn};${critical};0;${max}"

printf "%s - Total Users: %i%s\n" "$status" "$t_user" "$perf"
printf "Total Magnitude Users : %i\n" "$m_user"
printf "Total Web Users : %i\n" "$w_user"
printf "Total Excel Users : %i\n" "$e_user"
printf "Total Batch Users : %i\n" "$b_user"

exit $rc_code
