#!/bin/ksh
################################################################################
#
# check_datastore_sg_exchange.sh :
#          recuperation des filesize des datastore
#          par intermediere du script wmic
#
# Syntaxe: check_datastore_sg_exchange.sh -H host  -n num_sg
#          [ -p 'domain\user%mdp' ]
#
# Date creation: 29/12/2011
# Auteur: BAILAT Patrick
#
# Date modification: 10/05/2012
# Auteur: BAILAT Patrick
# Objet: ajoute d'une option permettant de preciser le domain compte et mot de 
#        passe a utiliser avec wmic 
#
# Date modification: 
# Auteur: 
# Objet: 
#
################################################################################

[ -n "$KSH_DEBUG" ] && set -x

# ===============================> variables <================================ #

typeset -i rc_code=0
typeset -i n_FLAG=0
typeset -i cmpt=0
status="OK"
warn=""
critical=""

# unite (users) et table par defaut
table="CIM_DataFile"
field="filesize"
message="Datastore size"
unit="B"

compte='corp\9NagiosDC%NglP(23M,n'
cmd="/usr/bin/wmic --namespace root/cimv2"

# ===============================> fonctions <================================ #

# usage (): affiche l'usage du script et sort du programme
#
usage ()
{
  mess="$1"
  usage_str="usage: %s -H host -n num_sg [-p 'domain\user%mdp'] " 

  printf "${mess}\n$usage_str" $prog_name
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

while getopts "H:n:p:" option
do
  case $option in
    H) host=$OPTARG;;
    p) compte=$OPTARG;;
    n) numsg="$OPTARG" 
       n_FLAG=1;;
  esac
done

# test des variables
[ -z "$host" ] && usage "host mandatory"
[ -z "$numsg" ] && usage "numero SG  mandatory"

# execution de la commande select par wmic
result=$($cmd -U $compte //$host "select $field from $table where Path=\"\\\\sg$numsg\\\\\" and filename like \"%sg$numsg%\"")
if [ $? -ne 0 ] 
then
    print "UNKNOWN - Invokation of wmic"
    exit 3
fi

print "$result" | tr "\\\\" "//" | while IFS='|' read valeur name
do
    # test que la variable contient que des chiffres 
    valtmp=$(print "$valeur" | sed "s/[0-9][0-9]*//g")
    [ -n "$valtmp" ] && continue

    # affectation de la valeur max
    [ -z "$max" ] && max=$((valeur+1)) 

    # name est vide (affectation du nom du champs suivi d'un compteur))
    if [ -z "$name" ]
    then
      if [ "$cmpt" -eq 0 ]
      then
        name=$field
        $((cmpt++))
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


    # Perfdata
    if [ -z "$perf" ]
    then
      perf="| $name=${valeur}${unit};${warn};${critical};0;${max}"
    else
      perf="$perf $name=${valeur}${unit};${warn};${critical};0;${max}"
    fi
done

print "$status - $message: $ls_valeur $perf\n" | tr '//' '\\'

exit $rc_code
