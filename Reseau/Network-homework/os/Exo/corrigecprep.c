#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h>
#include <errno.h>
#include <utime.h>
#include <stdarg.h>
#include <stdnoreturn.h>
#include <stdint.h>

#define	CHEMIN_MAX	512

#define	CHK(op)		do { if ((op) == -1) raler (1, #op) ; } while (0)

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

char *base (char *chemin)
{
    char *p ;

    p = strrchr (chemin, '/') ;
    return p == NULL ? chemin : p+1 ;
}

void copier_fichier (char *dst, char *src, size_t taille)
{
    int fdsrc, fddst ;
    char buf [taille] ;
    ssize_t nlus ;
    struct stat stbuf ;
    struct utimbuf t ;

    CHK (fdsrc = open (src, O_RDONLY)) ;
    CHK (fddst = open (dst, O_WRONLY | O_CREAT | O_TRUNC, 0666)) ;

    while ((nlus = read (fdsrc, buf, taille)) > 0)
	CHK (write (fddst, buf, nlus)) ;
    
    // On est sortis de la boucle soit parce que nlus = 0 (fin du fichier)
    // ou parce que nlus = -1 (erreur lors du read)
    CHK (nlus) ;

    CHK (fstat (fdsrc, &stbuf)) ;
    CHK (fchmod (fddst, stbuf.st_mode & 0777)) ;

    CHK (close (fdsrc)) ;
    CHK (close (fddst)) ;

    t.actime = stbuf.st_atime ;
    t.modtime = stbuf.st_mtime ;
    CHK (utime (dst, &t)) ;
}

int main (int argc, char *argv [])
{
    ssize_t taille ;
    char dest [CHEMIN_MAX + 1] ;
    char *rep ;
    int n, i ;
    char *b ;

    if (argc < 4)
	raler (0, "usage: cprep taille rep f1 ... fn") ;

    taille = atol (argv [1]) ;
    if (taille <= 0)
	raler (0, "la taille doit être > 0") ;

    rep = argv [2] ;
    if (mkdir (rep, 0777) == -1)
    {
	// Ce cas teste si l'erreur est due à autre chose qu'un fichier
	// (répertoire, mais aussi régulier ou autre) existant.
	// Si c'est autre chose qu'un répertoire, l'erreur sera détectée
	// lorsqu'on cherchera à créer un fichier dans ce répertoire.
	if (errno != EEXIST)
	    raler (1, "mkdir") ;
    }

    // Traiter tous les fichiers fournis sur la ligne de commande
    for (i = 3 ; i < argc ; i++)
    {
	// Déterminer le chemin du fichier destination
	b = base (argv [i]) ;
	n = snprintf (dest, sizeof dest, "%s/%s", rep, b) ;
	if (n < 0 || n > CHEMIN_MAX)
	    raler (0, "chemin '%s/%s' trop long", rep, b) ;

	copier_fichier (dest, argv [i], taille) ;
    }

    exit (0) ;
}
