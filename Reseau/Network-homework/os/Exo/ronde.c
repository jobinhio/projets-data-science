#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>			// pour les msg d'erreur uniquement
#include <inttypes.h>			// intmax_t
#include <stdnoreturn.h>		// C norme 2011
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <errno.h>
#include <signal.h>

#define	CHK(op)		do { if ((op) == -1) raler (1, #op) ; } while (0)

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

/******************************************************************************
 * Q1
 */

void args (int argc, char *argv [], char **fich, int tv [], int *pn)
{
    int i ;

    if (argc < 3 || argc - 2 > *pn)
	raler (0, "usage : ronde fichier v0 [v1 ... vn-1]") ;
    *fich = argv [1] ;
    for (i = 2 ; i < argc ; i++)
	tv [i-2] = atoi (argv [i]) ;
    *pn = argc - 2 ;
}

/******************************************************************************
 * Q2
 */

volatile sig_atomic_t recu1 = 0, recu2 = 0 ;

void handler (int num)
{
    switch (num)
    {
	case SIGUSR1 :
	    recu1 = 1 ;
	    break ;

	case SIGUSR2 :
	    recu2 = 1 ;
	    break ;

	default :
	    raler (0, "recu signal inconnu %d\n", num) ;
    }
}

void preparer_signaux (void)
{
    struct sigaction s ;

    s.sa_handler = handler ;
    s.sa_flags = 0 ;
    CHK (sigemptyset (&s.sa_mask)) ;
    CHK (sigaction (SIGUSR1, &s, NULL)) ;
    CHK (sigaction (SIGUSR2, &s, NULL)) ;
}

/******************************************************************************
 * Q3
 */

void attendre_signal (int signum)
{
    sigset_t masque, vide, ancien ;

    CHK (sigemptyset (&vide)) ;
    CHK (sigemptyset (&masque)) ;
    CHK (sigaddset (&masque, signum)) ;
    CHK (sigprocmask (SIG_BLOCK, &masque, &ancien)) ;
    if (signum == SIGUSR1 && ! recu1)
	sigsuspend (&vide) ;
    if (signum == SIGUSR2 && ! recu2)
	sigsuspend (&vide) ;
    CHK (sigprocmask (SIG_SETMASK, &ancien, NULL)) ;
}

/******************************************************************************
 * Q4
 */

void fils (const char *fichier, int i, int vi)
{
    int fd, n, k, v ;
    struct stat stbuf ;
    pid_t pidk ;

    attendre_signal (SIGUSR1) ;
    CHK (fd = open (fichier, O_RDWR)) ;
    CHK (fstat (fd, &stbuf)) ;
    n = stbuf.st_size / sizeof (pid_t) ;

    k = (i + 1) % n ;
    CHK (lseek (fd, k * sizeof (pid_t), SEEK_SET)) ;
    CHK (read (fd, &pidk, sizeof (pid_t))) ;

    CHK (lseek (fd, k * sizeof (pid_t), SEEK_SET)) ;
    CHK (write (fd, &vi, sizeof (pid_t))) ;

    CHK (kill (pidk, SIGUSR2)) ;

    attendre_signal (SIGUSR2) ;
    CHK (lseek (fd, i * sizeof (pid_t), SEEK_SET)) ;
    CHK (read (fd, &v, sizeof (pid_t))) ;
    printf ("p%d : lu %d\n", i, v) ;

    CHK (close (fd)) ;

    exit (0) ;
}

/******************************************************************************
 * Q5
 */

void lancer (const char *fichier, const int tv [], int n)
{
    int i, fd ;
    pid_t pid [n] ;

    CHK (fd = open (fichier, O_WRONLY | O_CREAT | O_TRUNC, 0666)) ;

    for (i = 0 ; i < n ; i++)
    {
	switch (pid [i] = fork ())
	{
	    case -1 :
		raler (1, "fork %d\n", i) ;

	    case 0 :
		fils (fichier, i, tv [i]) ;
		exit (1) ;

	    default :
		break ;
	}
    }

    CHK (write (fd, pid, sizeof (pid))) ;
    CHK (close (fd)) ;

    for (i = 0 ; i < n ; i++)
	CHK (kill (pid [i], SIGUSR1)) ;
}


/******************************************************************************
 * Q6
 */

#define	MAX	100

int main (int argc, char *argv [])
{
    char *fichier ;
    int tv [MAX] ;
    int i, n, raison, r ;

    n = MAX ;
    args (argc, argv, &fichier, tv, &n) ;

    preparer_signaux () ;	// Q7 : dans le père, avant de générer les fils
    lancer (fichier, tv, n) ;

    r = 0 ;
    for (i = 0 ; i < n ; i++)
    {
	CHK (wait (&raison)) ;
	if (! (WIFEXITED (raison) && WEXITSTATUS (raison) == 0))
	    r = 1 ;
    }

    CHK (unlink (fichier)) ;
    exit (r) ;
}
