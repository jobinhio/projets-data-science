#!/bin/sh

PROG=${PROG:=./distrib}			# chemin (relatif) de l'exécutable

TMP=${TMP:=/tmp/test}			# chemin des logs de test

#
# Script Shell de test de l'exercice 5
# Utilisation : sh ./test5.sh
#
# Si tout se passe bien, le script doit afficher "Tests ok" à la fin
# Dans le cas contraire, le nom du test échoué s'affiche.
# Les fichiers sont laissés dans /tmp/test1* en cas d'échec, vous
# pouvez les examiner.
# Pour avoir plus de détails sur l'exécution du script, vous pouvez
# utiliser :
#	sh -x ./test5.sh
# Toutes les commandes exécutées par le script sont alors affichées
# et vous pouvez les exécuter séparément.
#

# il ne faudrait jamais appeler cette fonction
# argument : message d'erreur
fail ()
{
    local msg="$1"

    echo FAIL				# aie aie aie...
    echo "$msg."
    exit 1
}

# Teste si un fichier est vide
# $1 = fichier
est_vide ()
{
    [ $# != 1 ] && fail "ERREUR SYNTAXE est_vide"
    local fichier="$1"
    test $(wc -l < "$fichier") = 0
}

# Vérifie que le message d'erreur est envoyé sur la sortie d'erreur
# et non sur la sortie standard
# $1 = nom du fichier de log (sans .err ou .out)
verifier_stderr ()
{
    [ $# != 1 ] && fail "ERREUR SYNTAXE verifier_stderr"
    local base="$1"
    est_vide $base.err \
	&& fail "Le message d'erreur devrait être sur la sortie d'erreur"
    est_vide $base.out \
	|| fail "Rien ne devrait être affiché sur la sortie standard"
}

# Vérifie que le message d'erreur indique la bonne syntaxe
# $1 = nom du fichier de log d'erreur
verifier_usage ()
{
    [ $# != 1 ] && fail "ERREUR SYNTAXE verifier_usage"
    local err="$1"
    local attendu="distrib n v1 ... vp"
    grep -q "usage *: $attendu" $err \
	|| fail "Message d'erreur devrait indiquer 'usage: $attendu'"
}

# retourne le numéro du dernier processus créé (cette fonction utilise 2 ps)
cur_ps ()
{
    echo blablabla > /dev/null &
    wait
    echo $!
}

verifier_nbproc ()
{
    [ $# != 2 ] && fail "ERREUR SYNTAXE verifier_nbproc"
    local nbatt="$1" pid1="$2"
    local nbproc pid2

    pid2=$(cur_ps)
    nbproc=$((pid2 - pid1 - 2))
    if [ $nbproc -lt $nbatt ]
    then fail "pas assez de processus ($nbproc < $nbatt)"
    fi
}

# vérifie la sortie dans $TMP.out par rapport aux arguments
# $1 = lignes attendues
verifier_res ()
{
    [ $# -lt 2 ] && fail "ERREUR SYNTAXE verifier_res"
    local out="$1" n="$2"
    shift 2

    local ftmp v p

    ftmp=$(sed 1q "$out")
    if [ -f "$ftmp" ]
    then fail "Fichier temporaire '$ftmp' toujours là"
    fi

    # extraire les affichages des fils
    sed 1d "$out" > $TMP.res

    # simuler la sortie attendue
    for v
    do
	p=$((v % n))
	echo "fils $p affiche $v"
    done > $TMP.att

    if diff $TMP.att $TMP.res > $TMP.dif
    then
	fail "Résultat != attendu. Voir $out, $TMP.att et $TMP.diff"
    fi
}

stress ()
{
    [ $# != 0 ] && fail "ERREUR SYNTAXE stress"
    while :
    do
	true
    done
}

# Supprimer les fichiers restant d'une précédente exécution
nettoyer ()
{
    chmod -R +rwx $TMP* 2> /dev/null
    rm -rf $TMP*
}


nettoyer

##############################################################################
# Vérification des arguments

# Quelques cas simples pour commencer

# # Est-ce que les messages d'erreur sont bien envoyés sur la sortie d'erreur ?
# echo "Test 1.1 - messages d'erreur sur la sortie d'erreur............ \c"
# $PROG > $TMP.out 2> $TMP.err
# est_vide $TMP.err && fail "message d'erreur devrait être sur stderr"
# est_vide $TMP.out || fail "rien ne devrait être affiché sur stdout"
# echo OK

# # Est-ce que le code de retour renvoyé (via exit) indique bien une
# # valeur différente de 0 en cas d'erreur ?
# echo "Test 1.2 - code de retour en cas d'erreur...................... \c"
# $PROG         2> $TMP.err
# [ $? = 0 ] && fail "en cas d'erreur, il faut utiliser exit(v) avec v!=0"
# echo OK

# # Test des arguments : nombre de processus invalide
# echo "Test 1.3 - nombre de processus invalide........................ \c"
# $PROG 0 1 > $TMP.out 2> $TMP.err && fail "n=0 => erreur => code de retour != 0"
# est_vide $TMP.err && fail "message d'erreur devrait être sur stderr"
# est_vide $TMP.out || fail "rien ne devrait être affiché sur stdout"
# echo OK

# # Test des arguments : valeur invalide
# echo "Test 1.4 - valeur invalide..................................... \c"
# $PROG 1 -1 > $TMP.out 2> $TMP.err && fail "v1=-1 => erreur => code de retour != 0"
# est_vide $TMP.err && fail "message d'erreur devrait être sur stderr"
# echo OK

# nettoyer

# ##############################################################################
# # Fonctionnalités basiques

# echo "Test 2.1 - test simple : un processus et une valeur............ \c"
# pid=$(cur_ps)
# $PROG 1 0 > $TMP.out 2> $TMP.err || fail "code de retour != 0"
# verifier_nbproc 2 $pid
# verifier_res $TMP.out 1 0
# echo OK

# echo "Test 2.2 - test plein de processus et aucune valeur............ \c"
# n=10
# pid=$(cur_ps)
# $PROG $n > $TMP.out 2> $TMP.err || fail "code de retour != 0"
# verifier_nbproc $n $pid
# verifier_res $TMP.out 10
# echo OK

# echo "Test 2.3 - un seul processus et plein de valeurs............... \c"
# n=1
# nval=10000
# pid=$(cur_ps)
# $PROG $n $(seq 1 $nval) > $TMP.out 2> $TMP.err || fail "code de retour != 0"
# verifier_nbproc $n $pid
# verifier_res $TMP.out 1 $(seq 1 $nval)
# echo OK

# echo "Test 2.4 - deux processus et plein de valeurs.................. \c"
# n=2
# nval=10000
# pid=$(cur_ps)
# $PROG $n $(seq $nval -1 1) > $TMP.out 2> $TMP.err || fail "code de retour != 0"
# verifier_nbproc $n $pid
# verifier_res $TMP.out $n $(seq $nval -1 1)
# echo OK

# echo "Test 2.5 - valeur invalide..................................... \c"
# nval=1000
# n=10
# pid=$(cur_ps)
# $PROG $n $(seq 1 $nval) -1  $(seq $nval -1 1) > $TMP.out 2> $TMP.err \
# 		&& fail "code de retour = 0 avec v = -1"
# echo OK

# echo "Test 2.6 - plein de processus et plein de valeurs.............. \c"
# nval=10000
# n=100
# pid=$(cur_ps)
# $PROG $n $(seq $nval -1 1) > $TMP.out 2> $TMP.err || fail "code de retour != 0"
# verifier_nbproc $n $pid
# verifier_res $TMP.out $n $(seq $nval -1 1)
# echo OK

##############################################################################
# Stress dû à une forte charge de processus

if command -v nproc > /dev/null
then coeurs=$(nproc)			# linuxism
else coeurs=16				# par défaut
fi
nstress=$((coeurs * 4))
liste=""
for i in $(seq $nstress)
do
    stress &
    liste="$liste $!"
done
# Terminer les processus en cas de sortie (prématurée ou non)
trap "kill -TERM $liste" EXIT	# terminer processus en cas de sortie
trap "kill -TERM $liste ; echo ; echo 'Test interrompu' >&2 ; exit 1" INT TERM
sleep 1			# laisser aux processus le temps de démarrer

echo "Test 3.1 - test simple : un processus et une valeur............ \c"
pid=$(cur_ps)
$PROG 1 0 > $TMP.out 2> $TMP.err || fail "code de retour != 0"
verifier_nbproc 2 $pid
verifier_res $TMP.out 1 0
echo OK

# echo "Test 3.2 - test plein de processus et aucune valeur............ \c"
# n=10
# pid=$(cur_ps)
# $PROG $n > $TMP.out 2> $TMP.err || fail "code de retour != 0"
# verifier_nbproc $n $pid
# verifier_res $TMP.out 10
# echo OK

# echo "Test 3.3 - un seul processus et plein de valeurs............... \c"
# n=1
# nval=10000
# pid=$(cur_ps)
# $PROG $n $(seq 1 $nval) > $TMP.out 2> $TMP.err || fail "code de retour != 0"
# verifier_nbproc $n $pid
# verifier_res $TMP.out 1 $(seq 1 $nval)
# echo OK

# echo "Test 3.4 - deux processus et plein de valeurs.................. \c"
# n=2
# nval=10000
# pid=$(cur_ps)
# $PROG $n $(seq $nval -1 1) > $TMP.out 2> $TMP.err || fail "code de retour != 0"
# verifier_nbproc $n $pid
# verifier_res $TMP.out $n $(seq $nval -1 1)
# echo OK

# echo "Test 3.5 - valeur invalide..................................... \c"
# nval=1000
# n=10
# pid=$(cur_ps)
# $PROG $n $(seq 1 $nval) -1  $(seq $nval -1 1) > $TMP.out 2> $TMP.err \
# 		&& fail "code de retour = 0 avec v = -1"
# echo OK

# echo "Test 3.6 - plein de processus et plein de valeurs.............. \c"
# nval=10000
# n=100
# pid=$(cur_ps)
# $PROG $n $(seq $nval -1 1) > $TMP.out 2> $TMP.err || fail "code de retour != 0"
# verifier_nbproc $n $pid
# verifier_res $TMP.out $n $(seq $nval -1 1)
# echo OK

nettoyer
echo "Tests ok"

exit 0
