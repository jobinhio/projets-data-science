#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h>
#include <errno.h>
#include <stdarg.h>
#include <stdnoreturn.h>
#include <stdint.h>

#define	CHK(op)		do { if ((op) == -1) raler (1, #op) ; } while (0)
#define	CHKN(op)	do { if ((op) == NULL) raler (1, #op) ; } while (0)

#define	CHEMIN_MAX	512

struct nom
{
    char chemin [CHEMIN_MAX + 1] ;
    struct nom *suiv ;
} ;

struct inode
{
    ino_t num ;			// numéro de l'inode
    nlink_t nliens ;		// nombre de noms trouvés
    struct nom *noms ;		// les différents noms trouvés pour cet inode
    struct inode *suiv ;
} ;

noreturn void raler (int syserr, const char *fmt, ...)
{
    va_list ap ;

    va_start (ap, fmt) ;
    vfprintf (stderr, fmt, ap) ;
    fprintf (stderr, "\n") ;
    va_end (ap) ;
    if (syserr)
	perror ("") ;
    exit (1) ;
}

// assertion : longueur(chemin) <= CHEMIN_MAX
struct inode *ajouter (struct inode *tete, ino_t num, char *chemin)
{
    struct inode *p ;
    struct nom *q ;

    // assert (strlen (chemin) <= CHEMIN_MAX) ;
    p = tete ;
    while (p != NULL && p->num != num)
	p = p->suiv ;

    // 2 cas possibles : p == NULL (non trouvé) ou p != NULL (inode trouvé)
    if (p == NULL)
    {
	CHKN (p = malloc (sizeof *p)) ;
	p->num = num ;
	p->nliens = 0 ;
	p->noms = NULL ;	// liste des noms trouvés = vide
	p->suiv = tete ;
	tete = p ;
    }

    // qd on arrive ici, p pointe sur l'élément trouvé
    CHKN (q = malloc (sizeof *q)) ;
    strcpy (q->chemin, chemin) ;
    q->suiv = p->noms ;
    p->noms = q ;
    p->nliens++ ;

    return tete ;
}

struct inode *parcourir (char *rep, struct inode *tete)
{
    DIR *dp ;
    struct dirent *d ;
    char nch [CHEMIN_MAX + 1] ;		// nouveau chemin
    int n ;
    struct stat stbuf ;


    CHKN (dp = opendir (rep)) ;
    while ((d = readdir (dp)) != NULL)
    {
	if (strcmp (d->d_name, ".") != 0 && strcmp (d->d_name, "..") != 0)
	{
	    n = snprintf (nch, CHEMIN_MAX+1, "%s/%s", rep, d->d_name) ;
	    if (n < 0 || n > CHEMIN_MAX)
		raler (0, "chemin '%s/%s' trop long", rep, d->d_name) ;

	    CHK (lstat (nch, &stbuf)) ;
	    switch (stbuf.st_mode & S_IFMT)
	    {
		case S_IFDIR :		// répertoire
		    tete = parcourir (nch, tete) ;
		    break ;
		case S_IFREG :		// fichier régulier
		    if (stbuf.st_nlink > 1)
			tete = ajouter (tete, stbuf.st_ino, nch) ;
		    break ;
		default :		// le reste
		    // ces cas sont ignorés
		    break ;
	    }
	}
    }
    CHK (closedir (dp)) ;

    return tete ;
}

void afficher (struct inode *tete)
{
    struct inode *p ;
    struct nom *q ;

    p = tete ;
    while (p != NULL)
    {
	if (p->nliens > 1)
	{
	    q = p->noms ;
	    while (q != NULL)
	    {
		/*********** : espace à afficher soit avant, soit après
		if (q != p->noms)
		    printf (" ") ;
		***********/
		printf ("%s", q->chemin) ;
		if (q->suiv != NULL)
		    printf (" ") ;
		q = q->suiv ;
	    }
	    printf ("\n") ;
	}
	p = p->suiv ;
    }
}

void liberer (struct inode *tete)
{
    struct inode *p, *psuiv ;
    struct nom *q, *qsuiv ;

    p = tete ;
    while (p != NULL)
    {
	psuiv = p->suiv ;
	q = p->noms ;
	while (q != NULL)
	{
	    qsuiv = q->suiv ;
	    free (q) ;
	    q = qsuiv ;
	}
	free (p) ;
	p = psuiv ;
    }
}

int main (int argc, char *argv [])
{
    struct inode *tete ;

    if (argc != 2)
	raler (0, "usage: liens repertoire") ;

    tete = NULL ;

    tete = parcourir (argv [1], tete) ;
    afficher (tete) ;
    liberer (tete) ;
    exit (0) ;
}
