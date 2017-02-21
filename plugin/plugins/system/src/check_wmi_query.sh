#!/bin/ksh
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
################################################################################
#
# check_wmi_query.sh :
#          Execution d'une commande 'select $field$ from $table$ $regex$'
#          par intermediere du script wmic
#          Recuperation de toute les lignes
#           (le  champ 'field doit etre un nombre)
#          Test les valeurs recuperees et affiche le status
#
# Syntaxe: check_wmi_query.sh -H host [ -f field -t table -r regex]
#                              [ -u unit] [-m message] [-w warn ] [-c critical]
#                              [ -p 'domain\user%mdp' ] [-i]
#
################################################################################

[ -n "$KSH_DEBUG" ] && set -x

# ===============================> variables <================================ #

typeset -i rc_code=0
typeset -i d_FLAG=0
typeset -i f_FLAG=0
typeset -i t_FLAG=0
typeset -i r_FLAG=0
typeset -i i_FLAG=0
typeset -i cmpt=0
status="OK"

# unite (users) et table par defaut
#table="CIM_DataFile"
#field="FileSize,name"
table="Win32_OperatingSystem"
field="CSName"

compte='corp\9NagiosDC%NglP(23M,n'
cmd="/usr/bin/wmic --namespace root/cimv2"

# ===============================> fonctions <================================ #

# usage (): affiche l'usage du script et sort du programme
#
usage ()
{
  mess="$1"
  usage_str="usage: %s -H host [-f field -t table ] [ -r regex] [-w warn]"
  usage_str="$usage_str [ -c critical] [-u unit] [-m message ]"
  usage_str="$usage_str [ -p \'domain\\\\user%%mdp\' ] [-i]"

  printf "${mess}\n${usage_str}\n" $prog_name
  exit 3
}

# calcul_max (): calcul le maximun pour le graph
#
calcul_max ()
{
  val=$1
  val1=$((val+1))

  if [ "$val1" -gt "$max" ]
  then
    max=$val1
  fi
}

# =================================> Main <=================================== #

while getopts "w:c:H:f:t:u:m:r:p:i" option
do
  case $option in
    w) warn=$OPTARG;;
    c) critical=$OPTARG;;
    H) host=$OPTARG;;
    p) compte=$OPTARG;;
    f) field=$OPTARG
       f_FLAG=1
       d_FLAG=1;;
    t) table=$OPTARG
       t_FLAG=1
       d_FLAG=1;;
    r) regex="$OPTARG"
       r_FLAG=1;;
    i) i_FLAG=1;;
    u) unit=$OPTARG;;
    m) message=$OPTARG;;
  esac
done

# test des variables
[ -z "$host" ] && usage "host mandatory"
[ -z "$field" ] && usage "field mandatory"
[ -z "$table" ] && usage "table mandatory"
[ "$d_FLAG" -eq 1 ] && [ "$f_FLAG" -ne 1 -o "$t_FLAG" -ne 1 ] && usage "field and table mandatory"
[ -z "$message" ] && message="$field"

# Run command "select" by wmic
result=$($cmd -U $compte //$host "select $field from $table $regex")
if [ $? -ne 0 ]
then
  if [ "$d_FLAG" -eq 1 ]
  then
    print "UNKNOWN - Invokation of wmic"
    exit 3
  fi

  status="CRITICAL"
  rc_code=2
  message="External command error"
fi

if [ -z "$result" ]
then
  if [ "$d_FLAG" -eq 1 ]
  then
    print "UNKNOWN - Error Execution Command (no result)"
    exit 3
  fi
fi

inverse=0
if [ "$d_FLAG" = 1 ]
then
  print "$result" | tr "\\\\" "//" | while read ligne
  do
    name_tmp=$(print "$ligne" | cut -d'|' -f2)
    valeur_tmp=$(print "$ligne" | cut -d'|' -f1)
    if [ "$valeur_tmp" = "Name" ]
    then
      inverse=1
    fi

    if [ $inverse -eq 1 ]
    then
       name=$valeur_tmp
       valeur=$name_tmp
    else
       name=$name_tmp
       valeur=$valeur_tmp
    fi

    # value have only nomber
    valtmp=$(print "$valeur" | sed "s/[0-9][0-9]*//g")
    [ -n "$valtmp" ] && continue

    # add value max
    [ -z "$max" ] && max=$((valeur+1))

    # name is empty ( add field and compteur))
    if [ -z "$name" -o "$name" = "$valeur" ]
    then
      if [ "$cmpt" -eq 0 ]
      then
        name=$field
        cmpt=$((cmpt++))
      else
        name="${field}$cmpt"
      fi
    fi

    # liste des valeurs
    if [ -z "$ls_valeur" ]
    then
      ls_valeur="$name $valeur"
    else
      ls_valeur="$ls_valeur\n$name $valeur"
    fi

    # verifie si au dessus du seuil warn
    if [ -n "$warn" ]
    then
      calcul_max $warn
      if [ "$i_FLAG" -eq 1 ]
      then
        if [ "$valeur" -lt "$warn" ]
        then
          status="WARNING"
          [ "$rc_code" -lt 1 ] && rc_code=1
        fi
      else
        if [ "$valeur" -ge "$warn" ]
        then
          calcul_max $valeur
          status="WARNING"
          [ "$rc_code" -lt 1 ] && rc_code=1
        fi
      fi
    fi

    # verifie si au dessus du seuil critical
    if [ -n "$critical" ]
    then
      calcul_max $critical
      if [ "$i_FLAG" -eq 1 ]
      then
        if [ "$valeur" -lt "$critical" ]
        then
          status="CRITICAL"
          rc_code=2
        fi
      else
        if [ "$valeur" -ge "$critical" ]
        then
          calcul_max $valeur
          status="CRITICAL"
          rc_code=2
      fi
      fi
    fi

    # Perfdata
    if [ -z "$perf" ]
    then
      perf="| $name=${valeur}${unit};${warn};${critical};-1;${max}"
    else
      perf="$perf $name=${valeur}${unit};${warn};${critical};-1;${max}"
    fi
  done
else
  ls_valeur=$(print "$result" | tail -n1 | tr '|' '\n')
fi

print "$status - $message: $ls_valeur $perf\n" | tr '//' '\\'

exit $rc_code
