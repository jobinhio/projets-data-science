#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <dirent.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <errno.h>
#include <stdarg.h>
#include <stdnoreturn.h>
#include <stdint.h>

#define	CHK(op)		do { if ((op) == -1) raler (1, #op) ; } while (0)
#define	CHKN(op)	do { if ((op) == NULL) raler (1, #op) ; } while (0)

#define	CHEMIN_MAX	128
#define	TAILLE_BUFFER	4096

struct msg
{
    char chemin [CHEMIN_MAX + 1] ;
    off_t nb ;
    int numproc ;
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

// explore l'arborescence indiquée par rep et génère les résultats dans fd_out
void explorateur (char *rep, int fd_out)
{
    struct stat stbuf ;
    char nchemin [CHEMIN_MAX + 1] ;
    DIR *dp ;
    struct dirent *d ;
    int n ;

    CHKN (dp = opendir (rep)) ;
    while ((d = readdir (dp)) != NULL)
    {
	if (strcmp (d->d_name, ".") != 0 && strcmp (d->d_name, "..") != 0)
	{
	    n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, d->d_name) ;
	    if (n < 0 || n > CHEMIN_MAX)
		raler (0, "chemin '%s/%s' trop long", rep, d->d_name) ;

	    CHK (lstat (nchemin, &stbuf)) ;
	    switch (stbuf.st_mode & S_IFMT)
	    {
		case S_IFDIR :
		    explorateur (nchemin, fd_out) ;
		    break ;

		case S_IFREG :
		    CHK (write (fd_out, nchemin, CHEMIN_MAX + 1)) ;
		    break ;

		default :
		    // ignorer les autres types de fichiers
		    break ;
	    }
	}
    }
    CHK (closedir (dp)) ;
}

// lit les chemins sur fd_in, écrit les résultats sur fd_out
void compteur (int fd_in, int fd_out, int moi, int car)
{
    ssize_t nlus, nlus2 ;
    char buffer [TAILLE_BUFFER] ;
    int fd, i ;
    struct msg m ;

    m.numproc = moi ;
    while ((nlus = read (fd_in, m.chemin, CHEMIN_MAX + 1)) > 0)
    {
	m.nb = 0 ;
	CHK (fd = open (m.chemin, O_RDONLY)) ;
	while ((nlus2 = read (fd, buffer, TAILLE_BUFFER)) > 0)
	    for (i = 0 ; i < nlus2 ; i++)
		if (buffer [i] == car)
		    m.nb++ ;
	// quand on arrive ici, nlus2 peut valoir 0 (ok) ou -1 (erreur)
	CHK (nlus2) ;
	CHK (close (fd)) ;
	CHK (write (fd_out, &m, sizeof m)) ;
    }
    // quand on arrive ici, nlus peut valoir 0 (ok) ou -1 (erreur)
    CHK (nlus) ;
}

void afficheur (int fd_in)
{
    ssize_t nlus ;
    struct msg m ;

    while ((nlus = read (fd_in, &m, sizeof m)) > 0)
	printf ("%s %jd %d\n", m.chemin, (intmax_t) m.nb, m.numproc) ;
    CHK (nlus) ;
}

int main (int argc, char *argv [])
{
    int i, nproc, raison, tube_entree [2], tube_sortie [2] ;

    if (argc != 4)
	raler (0, "usage: parcount répertoire caractère nproc") ;

    if (strlen (argv [2]) != 1)
	raler (0, "caractère doit être unique") ;
    nproc = atoi (argv [3]) ;
    if (nproc < 1)
	raler (0, "nproc doit être >= 1") ;

    CHK (pipe (tube_entree)) ;
    CHK (pipe (tube_sortie)) ;

    for (i = 0 ; i < nproc ; i++)
    {
	switch (fork ())
	{
	    case -1 :
		raler (1, "démarrage processus %d", i) ;

	    case 0 :
		CHK (close (tube_entree [1])) ;
		CHK (close (tube_sortie [0])) ;
		compteur (tube_entree [0], tube_sortie [1], i, argv [2][0]) ;
		CHK (close (tube_entree [0])) ;	// pas absolument indispensable
		CHK (close (tube_sortie [1])) ; // ... car exit juste après
		exit (0) ;

	    default :
		break ;
	}
    }

    CHK (close (tube_entree [0])) ;
    CHK (close (tube_sortie [1])) ;

    // restent ouverts : tube_entree [1], tube_sortie [0]

    switch (fork ())
    {
	case -1 :
	    raler (1, "démarrage processus afficheur", i) ;

	case 0 :
	    CHK (close (tube_entree [1])) ;
	    afficheur (tube_sortie [0]) ;
	    CHK (close (tube_sortie [0])) ;
	    exit (0) ;

	default :
	    break ;
    }

    CHK (close (tube_sortie [0])) ;
    explorateur (argv [1], tube_entree [1]) ;
    CHK (close (tube_entree [1])) ;

    for (i = 0 ; i <= nproc ; i++)
    {
	CHK (wait (&raison)) ;
	if (! (WIFEXITED (raison) && WEXITSTATUS (raison) == 0))
	    raler (0, "un fils s'est mal terminé") ;
    }

    exit (0) ;
}
