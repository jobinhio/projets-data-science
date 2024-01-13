#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <errno.h>
#include <stdarg.h>
#include <stdnoreturn.h>

#define	CHK(op)		do { if ((op) == -1) raler (1, #op) ; } while (0)
#define	CHKN(op)	do { if ((op) == NULL) raler (1, #op) ; } while (0)

/******************************************************************************
 * Gestion des erreurs
 */

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

char *lire_ligne (void)
{
    static char ligne [1000] ;
    int c, n ;

    n = 0 ;
    while ((c = getchar ()) != EOF && c != '\n')
	ligne [n++] = c ;
    ligne [n] = '\0' ;

    return (c == EOF && n == 0) ? NULL : ligne ;
}

/******************************************************************************
 * Q1
 */

char **creer_varg (int taille, char *vecteur [], char *ligne)
{
    char **nv ;
    int i ;

    CHKN (nv = calloc (taille + 2, sizeof (char *))) ;
    for (i = 0 ; i < taille ; i++)
	nv [i] = vecteur [i] ;
    nv [i++] = ligne ;
    nv [i] = NULL ;
    return nv ;
}

/******************************************************************************
 * Q2
 */

void executer (char *arguments [], int tube_w)
{
    char *err ;

    execvp (arguments [0], arguments) ;
    // si on arrive ici, c'est que execvp n'a pas fonctionné

    err = strerror (errno) ;
    CHK (write (tube_w, err, strlen (err) + 1)) ;
    CHK (close (tube_w)) ;
    exit (1) ;
}

/******************************************************************************
 * Q3
 */

void lancer_fils (char *vecteur [], int tube [])
{
    switch (fork ())
    {
	case -1 :
	    raler (0, "fork") ;

	case 0 :
	    CHK (close (tube [0])) ;
	    executer (vecteur, tube [1]) ;
	    exit (1) ;

	default :
	    CHK (close (tube [1])) ;
	    break ;
    }
}

/******************************************************************************
 * Q4
 */

int attendre_fils (int n)
{
    int i, raison, r ;

    r = 0 ;
    for (i = 0 ; i < n ; i++)
    {
	CHK (wait (&raison)) ;
	if (! (WIFEXITED (raison) && WEXITSTATUS (raison) == 0))
	    r = 1 ;
    }
    return r ;
}


/******************************************************************************
 * Q5
 */

int traiter_une_ligne (char *ligne, int argc, char *argv [])
{
    int tube [2] ;
    char **vecteur ;
    ssize_t nlus ;
    char message [1000] ;

    CHK (pipe (tube)) ;
    vecteur = creer_varg (argc - 1, argv + 1, ligne) ;
    lancer_fils (vecteur, tube) ;

    // exploiter le tube pour voir si le fils y a mis un message d'erreur
    CHK (nlus = read (tube [0], message, sizeof message)) ;
    CHK (close (tube [0])) ;

    if (nlus > 0)		// il y a eu une erreur lors de l'execvp
	fprintf (stderr, "erreur dans l'execvp du fils : %s\n", message) ;

    free (vecteur) ;

    return nlus > 0 ;		// 1 si erreur, 0 si pas d'erreur
}

/******************************************************************************
 * Q6
 */

int main (int argc, char *argv [])
{
    char *ligne ;
    int nproc, r ;

    nproc = 0 ;
    while ((ligne = lire_ligne ()) != NULL)
    {
	nproc++ ;
	if (traiter_une_ligne (ligne, argc, argv) != 0)
	    break ;
    }

    r = attendre_fils (nproc) ;
    exit (r != 0) ;		// 1 si erreur, 0 si pas d'erreur
}
