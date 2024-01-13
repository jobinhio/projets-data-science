#!/bin/sh

PROG=${PROG:=./prodscal}		# chemin (relatif) de l'exécutable

TMP=${TMP:=/tmp/test}			# chemin des logs de test

#
# Script Shell de test de l'exercice 3
# Utilisation : sh ./test3.sh
#
# Si tout se passe bien, le script doit afficher "Tests ok" à la fin
# Dans le cas contraire, le nom du test échoué s'affiche.
# Les fichiers sont laissés dans /tmp/test1* en cas d'échec, vous
# pouvez les examiner.
# Pour avoir plus de détails sur l'exécution du script, vous pouvez
# utiliser :
#	sh -x ./test3.sh
# Toutes les commandes exécutées par le script sont alors affichées
# et vous pouvez les exécuter séparément.
#

TMP=/tmp/test3

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
    grep -q "usage *: " $err \
	|| fail "Message d'erreur devrait indiquer 'usage:...'"
}

# retourne le numéro du dernier processus créé (cette fonction utilise 2 ps)
cur_ps ()
{
    echo blablabla > /dev/null &
    wait
    echo $!
}

# vérifie la sortie dans $TMP.out par rapport aux arguments
# args = lignes attendues
verif_res ()
{
    local i
    for i
    do
	echo $i
    done | diff -q - $TMP.out > /dev/null 2> /dev/null
    [ $? != 0 ] && fail "Résultat != attendu ($*). Voir $TMP.out"
}

# vérifie le temps d'exécution avec la commande time POSIX
# $1 = nom du fichier d'erreur écrit par time
# $2 = durée attendue min
# $3 = durée attendue max
verif_duree ()
{
    local fichier="$1" min="$2" max="$3"
    local duree_s duree_ms

    duree_s=$(sed -n 's/real *//p' "$fichier")
    duree_ms=$(echo "$duree_s*1000" | bc | sed 's/\..*//')

    if [ "$duree_ms" -lt "$min" ] || [ "$duree_ms" -gt "$max" ]
    then fail "durée incorrecte ($duree_ms ms) pas dans [$min,$max]"
    fi
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

# Est-ce que les messages d'erreur sont bien envoyés sur la sortie d'erreur ?
echo -n "Test 1.1 - messages d'erreur sur la sortie d'erreur............ "
$PROG > $TMP.out 2> $TMP.err
est_vide $TMP.err && fail "message d'erreur devrait être sur stderr"
est_vide $TMP.out || fail "rien ne devrait être affiché sur stdout"
echo OK

# Est-ce que le code de retour renvoyé (via exit) indique bien une
# valeur différente de 0 en cas d'erreur ?
echo -n "Test 1.2 - code de retour en cas d'erreur...................... "
$PROG         2> $TMP.err
[ $? = 0 ] && fail "en cas d'erreur, il faut utiliser exit(v) avec v!=0"
echo OK

# Test des arguments : nombre invalide
echo -n "Test 1.3 - nombre d'arguments invalide (0)..................... "
$PROG         2> $TMP.err && fail "0 argument => erreur => code de retour != 0"
verifier_usage $TMP.err
echo OK

# Test des arguments : nombre invalide
echo -n "Test 1.4 - nombre d'arguments invalide (2)..................... "
$PROG 0 1     2> $TMP.err && fail "2 args => erreur => code de retour != 0"
verifier_usage $TMP.err
echo OK

# Test des arguments : nombre invalide
echo -n "Test 1.5 - nombre d'arguments invalide (4)..................... "
$PROG 0 1 2 3 2> $TMP.err && fail "4 args => erreur => code de retour != 0"
verifier_usage $TMP.err
echo OK

# Délai invalide (on doit le tester dans le programme)
echo -n "Test 1.6 - délai invalide...................................... "
$PROG -1 1 2  2> $TMP.err && fail "délai invalide"
est_vide $TMP.err	  && fail "msg d'erreur devrait être sur stderr"
echo OK

nettoyer

##############################################################################
# Fonctionnalités basiques

echo -n "Test 2.1 - produit scalaire de deux vecteurs de dimension 1.... "
$PROG 0 3 4 > $TMP.out 2> $TMP.err || fail "code de retour != 0"
est_vide $TMP.err		|| fail "stderr non vide"
verif_res 12
echo OK

echo -n "Test 2.2 - produit scalaire de deux vecteurs de dim > 1........ "
$PROG 0 1 2 3 4 5 6 > $TMP.out 2> $TMP.err || fail "code de retour != 0"
est_vide $TMP.err		|| fail "stderr non vide"
verif_res 32
echo OK

echo -n "Test 2.3 - vérification du nombre de processus................. "
pid1=$(cur_ps)
$PROG 0 $(seq 1 20) > $TMP.out 2> $TMP.err || fail "code de retour != 0"
pid2=$(cur_ps)
est_vide $TMP.err		|| fail "stderr non vide"
verif_res 935
# il doit y avoir au minimum 1 (main) + 10 (fils) + 3 (2*cur_ps) = 14 processus
att=14
nproc=$((pid2 - pid1))
[ $nproc -le $att ] || fail "pas assez de processus ($nproc au lieu de $att)"
echo OK

echo -n "Test 2.4 - prise en compte du délai (2 secondes)............... "
TIME=$(command -v -p time)		# la commande POSIX time
# comme les fils sont démarrés en parallèle, la durée totale doit être
# le maximum des durées pseudo-aléatoires
$TIME -p $PROG 2000 $(seq 1 20) > $TMP.out 2> $TMP.err \
				|| fail "code de retour != 0"
verif_res 935
# si la distribution des nombres aléatoires est bien répartie, la moitié
# des 10 fils devrait attendre entre 1 et 2 secondes
verif_duree $TMP.err 1000 2100		# tolérance 100 ms : machines lentes
echo OK

echo -n "Test 2.5 - vérification du code retour de expr................. "
$PROG 0 1 2 3bla 4 5 6 > $TMP.out 2> $TMP.err && fail "code de retour = 0"
est_vide $TMP.out		|| fail "stdout non vide"
echo OK

nettoyer

##############################################################################
# Cas aux limites

NSEC=5
echo -n "Test 3.1 - délai non identique entre tous les fils ($NSEC sec)..... "
killall $PROG > /dev/null 2> /dev/null
nps0=$(ps | wc -l)		# nb de processus à l'état initial
ndecr=0				# nb de fois où c'est décrémenté
$PROG ${NSEC}000 $(seq 1 20) > $TMP.out 2> $TMP.err &
nps=$(ps | wc -l)
npsprec=$nps
for i in $(seq 1 $((NSEC*2)) )
do
    nps=$(ps | wc -l)
    if [ $nps -lt $npsprec ]
    then
	ndecr=$((ndecr+1))
	npsprec=$nps
    fi
    sleep 0.5
done
wait				# attendre le résultat final
est_vide $TMP.err		|| fail "stderr non vide"
verif_res 935
[ $ndecr -lt $(( NSEC / 2)) ] \
	&& fail "nb de ps pas suffisamment décroissant dans le temps"
echo OK

echo -n "Test 3.2 - suppression des fichiers temporaires................ "
PROGABS=$(pwd)/$PROG
[ -x $PROGABS ] || fail "Programme '$PROGABS' non trouvé"
mkdir $TMP.d
( cd $TMP.d ; $PROGABS 0 $(seq 1 20)) > $TMP.out 2> $TMP.err \
				|| fail "code de retour != 0"
est_vide $TMP.err		|| fail "stderr non vide"
verif_res 935
nfic=$(ls $TMP.d | wc -l)
[ $nfic != 0 ]			&& fail "il reste '$nfic' fichiers dans $TMP.d"
echo OK

MAX=999999999			# valeur max

echo -n "Test 3.3 - produits donnant un résultat trop grand............. "
# il faut vérifier les résultats intermédiaires de expr
$PROG 0 1 $MAX 3 4 10 6 > $TMP.out 2> $TMP.err \
				&& fail "code de retour = 0"
est_vide $TMP.out		|| fail "stdout non vide"
echo OK

echo -n "Test 3.4 - valeur fournie trop grande.......................... "
# la valeur trop grande doit être détectée au retour d'un expr
$PROG 0 1 2 $((MAX+1)) 10 3 4 > $TMP.out 2> $TMP.err \
				&& fail "code de retour = 0"
est_vide $TMP.out		|| fail "stdout non vide"
echo OK

echo -n "Test 3.5 - résultat final très grand mais non vérifié.......... "
# le résultat final ne peut/doit pas être vérifié
$PROG 0 1 1 1 1 $MAX $MAX $MAX $MAX > $TMP.out 2> $TMP.err \
				|| fail "code de retour != 0"
est_vide $TMP.err		|| fail "stderr non vide"
verif_res $((4*MAX))
echo OK

nettoyer
echo "Tests ok"

exit 0
