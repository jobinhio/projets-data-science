#!/bin/sh

PROG=${PROG:=./parcount}		# chemin (relatif) de l'exécutable

TMP=${TMP:=/tmp/test}			# chemin des logs de test

#
# Script Shell de test de l'exercice 4
# Utilisation : sh ./test4.sh
#
# Si tout se passe bien, le script doit afficher "Tests ok" à la fin
# Dans le cas contraire, le nom du test échoué s'affiche.
# Les fichiers sont laissés dans /tmp/test1* en cas d'échec, vous
# pouvez les examiner.
# Pour avoir plus de détails sur l'exécution du script, vous pouvez
# utiliser :
#	sh -x ./test4.sh
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
    local attendu="parcount répertoire caractère nproc"
    grep -q "usage *: $attendu" $err \
	|| fail "Message d'erreur devrait indiquer 'usage: $attendu'"
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

# retourne le numéro du dernier processus créé (cette fonction utilise 2 ps)
cur_ps ()
{
    echo blablabla > /dev/null &
    wait
    echo $!
}

# retourne le chemin et le nombre de caractères attendus
# $1 = chemin
# $2 = caractère cherché
attendu ()
{
    [ $# != 2 ] && fail "ERREUR SYNTAXE attendu"
    local chemin="$1" caractere="$2"
    local nb
    nb=$(tr -dc "$caractere" < "$chemin" | wc -c)
    echo "$chemin $nb"
}

# vérifie la sortie dans $TMP.out par rapport aux arguments
# $1 = lignes attendues
verif_res ()
{
    [ $# != 1 ] && fail "ERREUR SYNTAXE verif_res"
    local attendu="$1"
    echo "$attendu" | sort > $TMP.att
    # supprimer le numéro de processus
    sed 's/ [0-9][0-9]*$//' $TMP.out | sort | \
	diff - $TMP.att > $TMP.diff 2> /dev/null
    [ $? != 0 ] && fail "Résultat != attendu. Voir $TMP.out, $TMP.att et $TMP.diff"
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

# Test des arguments : nombre d'arguments invalide
echo -n "Test 1.3 - nombre d'arguments invalide......................... "
$PROG /tmp A  2> $TMP.err && fail "2 arguments => erreur => code de retour != 0"
verifier_usage $TMP.err
$PROG /tmp A 5 1  2> $TMP.err && fail "4 args => erreur => code de retour != 0"
verifier_usage $TMP.err
echo OK

# Test des arguments : caractère inexistant ou trop long
echo -n "Test 1.4 - caractère vide...................................... "
$PROG /tmp "" 1 > $TMP.out 2> $TMP.err && fail "caractère vide"
est_vide $TMP.err && fail "message d'erreur devrait être sur stderr"
est_vide $TMP.out || fail "rien ne devrait être affiché sur stdout"
$PROG /tmp AB 1 > $TMP.out 2> $TMP.err && fail "2 caractères"
est_vide $TMP.err && fail "message d'erreur devrait être sur stderr"
est_vide $TMP.out || fail "rien ne devrait être affiché sur stdout"
echo OK

# Test des arguments : nombre de processus invalide
echo -n "Test 1.5 - nombre de processus invalide........................ "
$PROG /tmp A 0 > $TMP.out 2> $TMP.err && fail "nproc=0 => erreur => code de retour != 0"
est_vide $TMP.err && fail "message d'erreur devrait être sur stderr"
est_vide $TMP.out || fail "rien ne devrait être affiché sur stdout"
echo OK

nettoyer

##############################################################################
# Fonctionnalités basiques

echo -n "Test 2.1 - répertoire simple et 1 processus.................... "
mkdir $TMP.d
echo AAAAAAAAAA > $TMP.d/dix
echo ABABABABABABABABABABABABABABABABABABABAB > $TMP.d/vingt
$PROG $TMP.d A 1 > $TMP.out 2> $TMP.err || fail "code de retour != 0"
est_vide $TMP.err		|| fail "stderr non vide"
ATTENDU="$TMP.d/dix 10
$TMP.d/vingt 20"
verif_res "$ATTENDU"
echo OK

echo -n "Test 2.2 - répertoire simple avec caractères aléatoires........ "
creer_fichier $TMP.d/alea 98765
nbA=$(tr -dc A < $TMP.d/alea | wc -c)
$PROG $TMP.d A 1 > $TMP.out 2> $TMP.err || fail "code de retour != 0"
est_vide $TMP.err		|| fail "stderr non vide"
ATTENDU="$TMP.d/dix 10
$TMP.d/vingt 20
$(attendu $TMP.d/alea A)"
verif_res "$ATTENDU"
echo OK

echo -n "Test 2.3 - arborescence simple et liens........................ "
mkdir $TMP.d/s1 $TMP.d/s1/s11 $TMP.d/s2
creer_fichier $TMP.d/s1/alea1.1 12345
creer_fichier $TMP.d/s1/alea1.2 23456
creer_fichier $TMP.d/s1/s11/alea11.1 34567
creer_fichier $TMP.d/s2/alea2.1 65432
ln -s $TMP.d/inexistant $TMP.d/lien
$PROG $TMP.d A 1 > $TMP.out 2> $TMP.err || fail "code de retour != 0"
est_vide $TMP.err		|| fail "stderr non vide"
ATTENDU="$TMP.d/dix 10
$TMP.d/vingt 20
$(attendu $TMP.d/alea A)
$(attendu $TMP.d/s1/alea1.1 A)
$(attendu $TMP.d/s1/alea1.2 A)
$(attendu $TMP.d/s1/s11/alea11.1 A)
$(attendu $TMP.d/s2/alea2.1 A)"
verif_res "$ATTENDU"
echo OK

##############################################################################
# Vérification des erreurs

nettoyer

echo -n "Test 3.1 - répertoire inaccessible............................. "
$PROG $TMP.d A 5 > $TMP.out 2> $TMP.err && fail "inexistant => exit != 0"
est_vide $TMP.err		&& fail "stderr non vide"
mkdir $TMP.d
chmod -r $TMP.d
$PROG $TMP.d A 5 > $TMP.out 2> $TMP.err && fail "non lisible => exit != 0"
est_vide $TMP.err		&& fail "stderr non vide"
chmod +r $TMP.d
echo OK

echo -n "Test 3.2 - fichier inaccessible................................ "
echo ABCDEF > $TMP.d/bla
chmod 0 $TMP.d/bla
$PROG $TMP.d A 5 > $TMP.out 2> $TMP.err && fail "non lisible => exit != 0"
est_vide $TMP.err		&& fail "stderr non vide"
nettoyer
echo OK

echo -n "Test 3.3 - longueur du chemin = 128 caractères................. "
mkdir $TMP.d
LIMITE=128
d=$TMP.d
l=$(echo -n $d | wc -c)
while [ $l -le $((LIMITE-2-11)) ]
do
    d=$d/1234567890
    l=$((l+11))
done
mkdir -p $d
n=$((LIMITE-l-1))
last=$(echo xxxxxxxxxxxxxxxx | cut -c 1-$((n-1)) )
base=$d/$last
creer_fichier ${base}a 1024
creer_fichier ${base}b 2048
$PROG $TMP.d A 5 > $TMP.out 2> $TMP.err \
		|| fail "Devrait autoriser lg de chemin = 128 caractères"
est_vide $TMP.err || fail "rien ne devrait être affiché sur stderr"
ATTENDU="$(attendu ${base}a A)
$(attendu ${base}b A)"
verif_res "$ATTENDU"
echo OK

echo -n "Test 3.4 - longueur du chemin = 129 caractères................. "
basey=${base}yy
creer_fichier ${base}yy 4096
$PROG $TMP.d A 5 > $TMP.out 2> $TMP.err \
		&& fail "Devrait interdire lg de chemin = 129 caractères"
est_vide $TMP.err && fail "stderr vide"
echo OK

##############################################################################
# Nombre de processus

nettoyer

echo -n "Test 4.1 - nombre de processus................................. "
mkdir $TMP.d
for i in $(seq 1 1000)
do
    creer_fichier $TMP.d/$i $((4567+i))
done
pid1=$(cur_ps)
$PROG $TMP.d A 100 > $TMP.out 2> $TMP.err || fail "code de retour != 0"
pid2=$(cur_ps)
est_vide $TMP.err		|| fail "stderr non vide"
# il doit y avoir au minimum 1 (main) + 100 (compteur) + 1 (afficheur) = 102 processus
att=102
nproc=$((pid2 - pid1))
[ $nproc -ge $att ] || fail "pas assez de processus ($nproc au lieu de $att)"
echo OK

echo -n "Test 4.2 - distribution des processus.......................... "
$PROG $TMP.d A 5 > $TMP.out 2> $TMP.err || fail "code de retour != 0"
# on devrait idéalement avoir 1000 / 5 = 200 fichiers par processus
min=100			# tolérance
max=300
i=0
sed 's/.* //' $TMP.out | sort | uniq -c > $TMP.nb
for n in $(sed 's/^ *\([0-9][0-9]*\) .*/\1/' $TMP.nb)
do
    if [ $n -lt $min ] || [ $n -gt $max ]
    then fail "processus $i a traité $n fichiers, $n pas dans [$min,$max]"
    fi
    i=$((i+1))
done
echo OK

nettoyer
echo "Tests ok"

exit 0
