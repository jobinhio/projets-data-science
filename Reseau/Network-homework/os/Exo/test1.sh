#!/bin/sh

PROG=${PROG:=./cprep}			# chemin de l'exécutable

TMP=${TMP:=/tmp/test}			# chemin des logs de test

#
# Script Shell de test de l'exercice 1
# Utilisation : sh ./test1.sh
#
# Si tout se passe bien, le script doit afficher "Tests ok" à la fin
# Les fichiers sont laissés dans /tmp/test* en cas d'échec, vous
# pouvez les examiner.
# Pour avoir plus de détails sur l'exécution du script, vous pouvez
# utiliser :
#	sh -x ./test1.sh
# Toutes les commandes exécutées par le script sont alors affichées
# et vous pouvez les exécuter séparément.
#

set -u					# erreur si variable non définie

# il ne faudrait jamais appeler cette fonction
# argument : message d'erreur
fail ()
{
    local msg="$1"

    echo FAIL				# aie aie aie...
    echo "$msg"
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
    grep -q "usage *: cprep " $err \
	|| fail "Message d'erreur devrait indiquer 'usage:...'"
}

# Vérifie que le programme n'affiche rien du tout
verifier_pas_de_sortie ()
{
    [ $# != 1 ] && fail "ERREUR SYNTAXE verifier_pas_de_sortie"
    local base="$1"
    est_vide $base.err \
	|| fail "Rien ne devrait être affiché sur la sortie d'erreur"
    est_vide $base.out \
	|| fail "Rien ne devrait être affiché sur la sortie standard"
}










# tester l'existence d'un fichier et la comparaison par rapport à un original
tester_original ()
{
    local fic="$1" org="$2" msg="$3"

    if [ ! -f "$fic" ]
    then fail "$msg : $fic non trouvé"
    fi
    if ! cmp -s "$org" "$fic"
    then fail "$msg : mauvaise copie de $fic (pas identique à $org)"
    fi
}

# vérifier les droits
tester_droits_date ()
{
    local repsrc="$1" repdst="$2" fic="$3" msg="$4"
    local dsrc ddst

    dsrc=$(cd "$repsrc" ; ls -l "$fic")
    ddst=$(cd "$repdst" ; ls -l "$fic")
    if [ x"$dsrc" != x"$ddst" ]
    then fail "$msg: droits/date différents ($dsrc != $ddst)"
    fi
}

# Supprimer les fichiers restant d'une précédente exécution
chmod -R +w $TMP* 2> /dev/null
rm -rf $TMP*

##############################################################################
# Vérification des arguments

# Est-ce que les messages d'erreur sont bien envoyés sur la sortie d'erreur ?
echo -n "Test 1.1 - Messages d'erreur sur la sortie d'erreur............ "
$PROG > $TMP.out 2> $TMP.err
verifier_stderr $TMP
verifier_usage $TMP.err
echo "OK"

# Est-ce que le code de retour renvoyé (via exit) indique bien une
# valeur différente de 0 en cas d'erreur ?
echo -n "Test 1.2 - Code de retour en cas d'erreur...................... "
$PROG > $TMP.out 2> $TMP.err
[ $? = 0 ] && fail "En cas d'erreur, il faut utiliser exit(v) avec v!=0"
verifier_stderr $TMP
verifier_usage $TMP.err
echo "OK"

# Nombre d'arguments
echo -n "Test 1.3 - Nombre d'arguments invalide......................... "
$PROG 10        > $TMP.out 2> $TMP.err \
		&& fail "1 arg => erreur => code de retour != 0"
verifier_stderr $TMP
verifier_usage $TMP.err

$PROG 10 $TMP.d > $TMP.out 2> $TMP.err \
		&& fail "2 arg => erreur => code de retour != 0"
verifier_stderr $TMP
verifier_usage $TMP.err
[ -d $TMP.d ] && fail "Répertoire créé alors qu'il y a eu une erreur"
echo "OK"

# Vérification de la taille
echo -n "Test 1.4 - Taille invalide..................................... "
rm -rf $TMP.*
touch $TMP.1
$PROG  0 $TMP.d $TMP.1 > $TMP.out 2> $TMP.err \
		&& fail "Taille de buffer invalide (0)"
verifier_stderr $TMP
[ -d $TMP.d ] && fail "Répertoire créé alors qu'il y a eu une erreur"
$PROG -1 $TMP.d $TMP.1 > $TMP.out 2> $TMP.err \
		&& fail "Taille de buffer invalide (-1)"
verifier_stderr $TMP
[ -d $TMP.d ] && fail "Répertoire créé alors qu'il y a eu une erreur"
echo "OK"

##############################################################################
# Création (ou non) du répertoire

# Création du répertoire
echo -n "Test 2.1 - Création du répertoire.............................. "
rm -rf $TMP.*
touch $TMP.1
$PROG 4096 $TMP.d $TMP.1 > $TMP.out 2> $TMP.err \
		|| fail "Erreur pour copie d'un fichier"
verifier_pas_de_sortie $TMP
[ -d $TMP.d ]	|| fail "Répertoire $TMP.d pas créé"
nfic=$(ls $TMP.d | wc -l)
[ $nfic = 1 ]	|| fail "Le répertoire ne contient pas un unique fichier"
echo "OK"

# Pas besoin de création si le répertoire existe déjà
echo -n "Test 2.2 - Utilisation d'un répertoire existant................ "
touch $TMP.2
$PROG 4096 $TMP.d $TMP.2 > $TMP.out 2> $TMP.err \
		|| fail "Erreur pour copie d'un deuxième fichier"
verifier_pas_de_sortie $TMP
nfic=$(ls $TMP.d | wc -l)
[ $nfic = 2 ]	|| fail "Le répertoire ne contient pas 2 fichiers"
echo "OK"

# Test d'erreur de création d'un répertoire invalide
echo -n "Test 2.3 - Erreur lors de la création du répertoire............ "
rm -rf $TMP.*
touch $TMP.d		# fichier régulier => création répertoire impossible
touch $TMP.1
$PROG 4096 $TMP.d $TMP.1 > $TMP.out 2> $TMP.err \
		&& fail "Détection d'erreur lors de la création du répertoire"
verifier_stderr $TMP
echo "OK"

# Test d'erreur de création d'un répertoire invalide
echo -n "Test 2.4 - Autre erreur lors de la création du répertoire...... "
rm -rf $TMP.*
mkdir $TMP.d
chmod -w $TMP.d		# répertoire $TMP.d non modifiable
touch $TMP.1
$PROG 4096 $TMP.d/toto $TMP.1 > $TMP.out 2> $TMP.err \
		&& fail "Détection d'erreur lors de la création du répertoire"
verifier_stderr $TMP
chmod +w $TMP.d
rm -rf $TMP.*
echo "OK"

# Test d'erreur de création d'un répertoire invalide
echo -n "Test 2.5 - Encore erreur lors de la création du répertoire..... "
rm -rf $TMP.*
mkdir $TMP.d
touch $TMP.1
$PROG 4096 $TMP.d/toto/titi $TMP.1 > $TMP.out 2> $TMP.err \
		&& fail "Détection d'erreur lors de la création du répertoire"
verifier_stderr $TMP
chmod +w $TMP.d
rm -rf $TMP.*
echo "OK"

##############################################################################
# Recopie des fichiers

echo -n "Test 3.1 - Recopie d'un fichier de taille nulle................ "
rm -rf $TMP.*
mkdir $TMP.d
touch $TMP.d/f1
$PROG 4096 $TMP.d/rep $TMP.d/f1 > $TMP.out 2> $TMP.err \
		|| fail "Recopie d'un fichier de taille nulle"
verifier_pas_de_sortie $TMP
cmp -s $TMP.d/f1 $TMP.d/rep/f1 || fail "Fichier recopié != original"
echo "OK"

echo -n "Test 3.2 - Recopie d'un fichier................................ "
rm -rf $TMP.*
mkdir $TMP.d
dd if=/dev/urandom bs=16383 count=1 of=$TMP.d/f1 2> /dev/null
$PROG 4096 $TMP.d/rep $TMP.d/f1 > $TMP.out 2> $TMP.err \
		|| fail "Recopie d'un fichier"
verifier_pas_de_sortie $TMP
cmp -s $TMP.d/f1 $TMP.d/rep/f1 || fail "Fichier recopié != original"
echo "OK"

echo -n "Test 3.3 - Recopie de plusieurs fichiers....................... "
n=16383
for i in 1 2 3
do
    dd if=/dev/urandom bs=$n count=1 of=$TMP.d/f$i 2> /dev/null
    n=$((n+1))
done
$PROG 4096 $TMP.d/rep $TMP.d/f? > $TMP.out 2> $TMP.err \
		|| fail "Recopie de 3 fichiers"
verifier_pas_de_sortie $TMP
for i in 1 2 3
do
    cmp -s $TMP.d/f$i $TMP.d/rep/f$i || fail "Fichier f$i != original"
done
echo "OK"

echo -n "Test 3.4 - Recopie des permissions et des dates................ "
rm -rf $TMP.d/rep
chmod 400 $TMP.d/f1 ; touch -d 2030-12-31T23:59 $TMP.d/f1
chmod 677 $TMP.d/f2 ; touch -d 2000-01-01T12:00 $TMP.d/f2
chmod 421 $TMP.d/f3
$PROG 4096 $TMP.d/rep $TMP.d/f? > $TMP.out 2> $TMP.err \
		|| fail "Recopie de 3 fichiers"
verifier_pas_de_sortie $TMP
# tester les permissions
for i in 1 2 3
do
    perm_orig=$(ls -l $TMP.d/f$i | sed 's/ .*//')
    perm_copie=$(ls -l $TMP.d/rep/f$i | sed 's/ .*//')
    [ x"$perm_copie" = x"$perm_orig" ] || fail "Permissions f$i != original"
done
# pour les dates, on ne teste que l'ordre des fichiers (suivant un tri par date)
liste=$(echo $(cd $TMP.d/rep ; ls -t))
[ "$liste" = "f1 f3 f2" ] || fail "Dates copies != original"
echo "OK"

echo -n "Test 3.5 - Recopie depuis plusieurs répertoires différents..... "
rm -rf $TMP.*
mkdir $TMP.d
liste="r1/r11/f1 r2/r21/f2 r2/r22/r221/f3 r1/r12/r121/f4"
args=""
for l in $liste
do
    dir=$(echo $l | sed 's:/f.*::')
    mkdir -p $TMP.d/$dir
    dd if=/dev/urandom bs=16383 count=1 of=$TMP.d/$l 2> /dev/null
    args="$args $TMP.d/$l"
done
$PROG 4096 $TMP.d/rep $args > $TMP.out 2> $TMP.err \
		|| fail "Recopie de plusieurs fichiers"
verifier_pas_de_sortie $TMP
for l in $liste
do
    f=$(echo $l | sed 's/.*f/f/')
    cmp -s $TMP.d/$l $TMP.d/rep/$f || fail "$TMP.d/$l != $TMP.d/rep/$f"
done
echo "OK"

##############################################################################
# Cas particuliers, cas aux limites

echo -n "Test 4.1 - Pas de création de fichier si original inexistant... "
rm -rf $TMP.*
mkdir $TMP.d
$PROG 4096 $TMP.d/rep $TMP.d/inexistant > $TMP.out 2> $TMP.err \
		&& fail "Fichier de détection de fichier inexistant"
verifier_stderr $TMP
# le fichier de sortie ne devrait pas être créé
[ -f $TMP.d/rep/inexistant ] \
		&& fail "Fichier destination ne devrait pas être créé"
echo "OK"

echo -n "Test 4.2 - Longueur du chemin = 512 caractères................. "
rm -rf $TMP.*
mkdir $TMP.d
LIMITE=512
d=$TMP.d
l=$(echo -n $d | wc -c)
while [ $l -le 500 ]
do
    d=$d/1234567890
    l=$((l+11))
done
mkdir -p $d
n=$((512-l-1))
last=$(echo xxxxxxxxxxxxxxxx | cut -c 1-$((n-1)) )
touch $TMP.d/$last
$PROG 4096 $d $TMP.d/$last > $TMP.out 2> $TMP.err \
		|| fail "Devrait autoriser lg de chemin = 512 caractères"
verifier_pas_de_sortie $TMP
[ -f $d/$last ] || fail "Copie devrait exister avec chemin de 512 caractères"
echo OK

echo -n "Test 4.3 - Longueur du chemin = 513 caractères................. "
lasty=${last}y
touch $TMP.d/$lasty
$PROG 4096 $d $TMP.d/$lasty > $TMP.out 2> $TMP.err \
		&& fail "Devrait interdire lg de chemin = 513 caractères"
verifier_stderr $TMP
[ -f $d/$lasty ] && fail "Fichier créé avec un chemin de 513 caractères"
echo OK

echo -n "Test 4.4 - Prise en compte de la taille (lent)................. "
rm -rf $TMP.*
mkdir $TMP.d
dureebloc=0.00
count=4
while [ $dureebloc = 0.00 ]
do
    dd if=/dev/urandom bs=1048576 count=$count of=$TMP.d/f1 2> /dev/null
    command -p time -p \
	$PROG 4096 $TMP.d/bloc $TMP.d/f1 > $TMP.out 2> $TMP.bloc \
		|| fail "Devrait fonctionner avec une grande taille"
    dureebloc=$(head -1 $TMP.bloc | sed -n 's/real //p')
    count=$((count+4))
done
command -p time -p \
	$PROG    1 $TMP.d/1    $TMP.d/f1 > $TMP.out 2> $TMP.1 \
		|| fail "Devrait fonctionner 1"
duree1=$(head -1 $TMP.1 | sed -n 's/real //p')
rapport=$(echo $duree1/$dureebloc | bc)
[ $rapport -gt 100 ] || fail "Durée anormalement rapide avec taille=1"
echo "OK"

rm -rf $TMP*

exit 0
