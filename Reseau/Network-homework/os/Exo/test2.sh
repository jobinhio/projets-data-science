#!/bin/sh

PROG=${PROG:=./liens}			# chemin de l'exécutable

TMP=${TMP:=/tmp/test}			# chemin des logs de test

#
# Script Shell de test de l'exercice 2
# Utilisation : sh ./test2.sh
#
# Si tout se passe bien, le script doit afficher "Tests ok" à la fin
# Dans le cas contraire, le nom du test échoué s'affiche.
# Les fichiers sont laissés dans /tmp/test1* en cas d'échec, vous
# pouvez les examiner.
# Pour avoir plus de détails sur l'exécution du script, vous pouvez
# utiliser :
#	sh -x ./test2.sh
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

# Crée un fichier de contenu de taille donnée et de contenu aléatoire
# $1 = chemin
# $2 = taille en octets
creer_fichier ()
{
    [ $# != 2 ] && fail "ERREUR SYNTAXE creer_fichier"
    local chemin="$1" taille=$2
    dd if=/dev/urandom bs=$taille count=1 of=$chemin 2> /dev/null
}

# Crée une arborescence minimale :
#	racine
#	 |- d1
#	 |   |-d11
#	 |   |  `-a (fichier simple)
#	 |   `-d12
#	 |- d2
#	 |   `-d21
#	 |      `-d (fichier simple)
#	 `- d3
#	     `-d31
# $1 = racine
creer_arbo ()
{
    [ $# != 1 ] && fail "ERREUR SYNTAXE creer_arbo"
    local racine="$1"

    mkdir -p $racine/d1/d11 $racine/d1/d12 $racine/d2/d21 $racine/d3/d31
    creer_fichier $racine/d1/d11/a 16383
    creer_fichier $racine/d2/d21/d 8193
}

# Tester si la sortie correspond au résultat attendu
# $1 = fichier de sortie
# $2 = contenu attendu
verifier_attendu ()
{
    [ $# != 2 ] && fail "ERREUR SYNTAXE verifier_attendu"
    local sortie=$1 attendu="$2"
    local nbout nbatt

    # la vérification est basique : on vérifie que le nombre
    # de lignes est le même
    nbout=$(wc -l < $sortie)
    nbatt=$(echo -n "$attendu" | wc -l)
    test $nbout = $nbatt \
    	|| fail "Nb fichiers trouvés ($nbout) != nb attendu ($nbatt)"

    # puis que tous les mots qui constituent les deux fichiers sont les mêmes
    tr ' ' '\n' < $sortie | sort > $TMP.out2
    echo -n "$attendu" | tr ' ' '\n' | sort > $TMP.att2
    diff $TMP.att2 $TMP.out2 > $TMP.diff \
    	|| fail "sortie non conforme (cf $TMP.diff)"
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
$PROG 2> $TMP.err
[ $? = 0 ] && fail "en cas d'erreur, il faut utiliser exit(v) avec v!=0"
echo OK

# Test des arguments : nombre invalide
echo -n "Test 1.3 - nombre d'arguments invalide (0)..................... "
$PROG 2> $TMP.err         && fail "0 argument => erreur => code de retour != 0"
verifier_usage $TMP.err
echo OK

# Test des arguments : nombre invalide
echo -n "Test 1.4 - nombre d'arguments invalide (2)..................... "
$PROG . . 2> $TMP.err     && fail "2 args => erreur => code de retour != 0"
verifier_usage $TMP.err
echo OK

# Le répertoire n'existe pas
echo -n "Test 1.5 - répertoire inexistant............................... "
rm -f $TMP.nonexistant		# on est vraiment sûr qu'il n'existe pas
$PROG $TMP.nonexistant > $TMP.out 2> $TMP.err && fail "devrait détecter une erreur"
est_vide $TMP.err	&& fail "msg d'erreur devrait être sur stderr"
echo OK

# Le répertoire n'est pas un répertoire
echo -n "Test 1.6 - argument pas un répertoire.......................... "
creer_fichier $TMP.fichier 127
$PROG $TMP.fichier > $TMP.out 2> $TMP.err && fail "devrait détecter une erreur"
est_vide $TMP.err	&& fail "msg d'erreur devrait être sur stderr"
echo OK

# Le répertoire n'est pas lisible
echo -n "Test 1.7 - répertoire non lisible.............................. "
mkdir $TMP.d
chmod 0400 $TMP.d
creer_fichier $TMP.fichier 127
$PROG $TMP.fichier > $TMP.out 2> $TMP.err && fail "devrait détecter une erreur"
est_vide $TMP.err	&& fail "msg d'erreur devrait être sur stderr"
echo OK

nettoyer

##############################################################################
# Arborescence basique

echo -n "Test 2.1 - arborescence vide................................... "
mkdir $TMP.d
$PROG $TMP.d > $TMP.out 2> $TMP.err || fail "code de retour devrait être nul"
est_vide $TMP.err	|| fail "rien ne devrait être affiché sur stderr"
est_vide $TMP.out	|| fail "rien ne devrait être affiché sur stdout"
echo OK

echo -n "Test 2.2 - arborescence simple sans liens multiples............ "
creer_fichier $TMP.d/x 4095
creer_fichier $TMP.d/y 8193
creer_fichier $TMP.d/z 1025
$PROG $TMP.d > $TMP.out 2> $TMP.err || fail "code de retour devrait être nul"
est_vide $TMP.err	|| fail "rien ne devrait être affiché sur stderr"
est_vide $TMP.out	|| fail "rien ne devrait être affiché sur stdout"
echo OK

echo -n "Test 2.3 - arborescence simple avec liens multiples............ "
ln $TMP.d/x $TMP.d/lien2
ln $TMP.d/x $TMP.d/lien3
ln $TMP.d/y $TMP.d/lien4
$PROG $TMP.d > $TMP.out 2> $TMP.err || fail "code de retour devrait être nul"
est_vide $TMP.err	|| fail "rien ne devrait être affiché sur stderr"
ATTENDU="$TMP.d/x $TMP.d/lien2 $TMP.d/lien3
$TMP.d/y $TMP.d/lien4
"
verifier_attendu $TMP.out "$ATTENDU"
echo OK

##############################################################################
# Arborescence plus complexe

nettoyer

echo -n "Test 3.1 - arborescence complexe sans liens multiples.......... "
creer_arbo $TMP.d
$PROG $TMP.d > $TMP.out 2> $TMP.err || fail "code de retour devrait être nul"
est_vide $TMP.err	|| fail "rien ne devrait être affiché sur stderr"
est_vide $TMP.out	|| fail "rien ne devrait être affiché sur stdout"
echo OK

echo -n "Test 3.2 - arborescence complexe avec liens multiples.......... "
ln $TMP.d/d1/d11/a $TMP.d/d1/d12/b
ln $TMP.d/d1/d11/a $TMP.d/d2/c
ln $TMP.d/d2/d21/d $TMP.d/e
$PROG $TMP.d > $TMP.out 2> $TMP.err || fail "code de retour devrait être nul"
est_vide $TMP.err	|| fail "rien ne devrait être affiché sur stderr"
ATTENDU="$TMP.d/d1/d11/a $TMP.d/d1/d12/b $TMP.d/d2/c
$TMP.d/d2/d21/d $TMP.d/e
"
verifier_attendu $TMP.out "$ATTENDU"
echo OK

echo -n "Test 3.3 - ignorer les liens symboliques....................... "
ln -s $TMP.d/d1/d11/a $TMP.d/d3/f
ln -s $TMP.d/non-existant $TMP.d/d3/g
$PROG $TMP.d > $TMP.out 2> $TMP.err || fail "code de retour devrait être nul"
est_vide $TMP.err	|| fail "rien ne devrait être affiché sur stderr"
ATTENDU="$TMP.d/d1/d11/a $TMP.d/d1/d12/b $TMP.d/d2/c
$TMP.d/d2/d21/d $TMP.d/e
"
verifier_attendu $TMP.out "$ATTENDU"
echo OK

echo -n "Test 3.4 - détecter les erreurs en profondeur.................. "
chmod 0 $TMP.d/d3
$PROG $TMP.d > $TMP.out 2> $TMP.err && fail "devrait détecter une erreur"
est_vide $TMP.err	&& fail "il devrait y avoir un message sur stderr"
est_vide $TMP.out	|| fail "on ne devrait rien afficher sur stdout"
echo OK

##############################################################################
# Cas particuliers, cas aux limites

nettoyer

echo -n "Test 4.1 - valgrind............................................ "
creer_arbo $TMP.d
ln $TMP.d/d1/d11/a $TMP.d/d1/d12/b
ln $TMP.d/d1/d11/a $TMP.d/d2/c
ln $TMP.d/d2/d21/d $TMP.d/e
valgrind --leak-check=full --error-exitcode=10 -q \
	$PROG $TMP.d > $TMP.out 2> $TMP.err \
	|| fail "échec avec valgrind, cf $TMP.err"
est_vide $TMP.err	|| fail "rien ne devrait être affiché sur stderr"
ATTENDU="$TMP.d/d1/d11/a $TMP.d/d1/d12/b $TMP.d/d2/c
$TMP.d/d2/d21/d $TMP.d/e
"
verifier_attendu $TMP.out "$ATTENDU"
echo OK

nettoyer

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
base=$d/$last
creer_fichier ${base}a 1024
creer_fichier ${base}b 2048
ln ${base}a $TMP.d/c
$PROG $TMP.d > $TMP.out 2> $TMP.err \
		|| fail "Devrait autoriser lg de chemin = 512 caractères"
est_vide $TMP.err || fail "rien ne devrait être affiché sur stderr"
ATTENDU="${base}a $TMP.d/c
"
verifier_attendu $TMP.out "$ATTENDU"
echo OK

echo -n "Test 4.3 - Longueur du chemin = 513 caractères................. "
basey=${base}yy
creer_fichier ${base}yy 4096
$PROG $TMP.d > $TMP.out 2> $TMP.err \
		&& fail "Devrait interdire lg de chemin = 513 caractères"
verifier_stderr $TMP
echo OK

nettoyer
echo "Tests ok"

exit 0
