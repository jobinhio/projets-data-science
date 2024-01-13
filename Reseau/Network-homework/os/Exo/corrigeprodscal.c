#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <stdarg.h>
#include <stdnoreturn.h>
#include <time.h>

#define	CHK(op)		do { if ((op) == -1) raler (1, #op) ; } while (0)

#define	CHEMIN_MAX	512

#define	TAILLE_MAX	sizeof ("999999999")	// 10 = 9 chiffres + \0

#define	RESULTAT	"res%d"

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

int main (int argc, const char *argv [])
{
    int delai, i, j, n, fd, delai_aleatoire, raison ;
    char chemin [CHEMIN_MAX] ;

    if (argc < 4 || argc % 2 != 0)
	raler (0, "usage : prodscal delai x1 ... xn y1 ... yn") ;

    delai = atoi (argv [1]) ;
    if (delai < 0)
	raler (0, "le délai doit être positif") ;

    n = (argc - 2) / 2 ;

    srand (time (NULL)) ;		// pas absolument nécessaire

    // première étape : lancer les "expr" dans des processus fils
    for (i = 0 ; i < n ; i++)
    {
	delai_aleatoire = rand () / ((double) RAND_MAX + 1) * (delai + 1) ;
	switch (fork ())
	{
	    case -1 :
		raler (1, "erreur fork sur fils %d", i) ;

	    case 0 :
		usleep (delai_aleatoire * 1000) ;
		(void) snprintf (chemin, sizeof chemin, RESULTAT, i) ;
		CHK (fd = open (chemin, O_WRONLY | O_CREAT | O_TRUNC, 0666)) ;
		CHK (dup2 (fd, 1)) ;
		CHK (close (fd)) ;
		execlp ("expr", "expr", argv [2+i], "*", argv[2+n+i], NULL) ;
		// si on arrive ici, c'est execlp n'a pas réussi
		raler (1, "expr fils %d", i) ;

	    default :
		break ;
	}
    }

    // deuxième étape : attendre la terminaison des processus fils
    for (i = 0 ; i < n ; i++)
    {
	CHK (wait (&raison)) ;
	if (! (WIFEXITED (raison) && WEXITSTATUS (raison) == 0))
	    raler (0, "un fils s'est mal terminé") ;
    }

    // troisième étape : lire les résultats des xi*yi
    char tabarg [n][TAILLE_MAX+1] ;	// +1 pour détecter les dépassements
    char *nargv [1 + n + n-1 + 1] ;
    j = 0 ;
    nargv [j++] = "expr" ;

    for (i = 0 ; i < n ; i++)
    {
	ssize_t nlus ;

	(void) snprintf (chemin, sizeof chemin, RESULTAT, i) ;
	CHK (fd = open (chemin, O_RDONLY)) ;
	CHK (nlus = read (fd, tabarg [i], TAILLE_MAX+1)) ;
	CHK (close (fd)) ;
	CHK (unlink (chemin)) ;
	if ((size_t) nlus > TAILLE_MAX)
	    raler (0, "nombre trop grand") ;
	tabarg [i][nlus-1] = '\0' ;

	if (i > 0)
	    nargv [j++] = "+" ;
	nargv [j++] = tabarg [i] ;
    }
    nargv [j] = NULL ;    

    // quatrième étape : c'est le calcul final
    execvp ("expr", nargv) ;
    raler (1, "expr final") ;
}
