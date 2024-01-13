#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <errno.h>
#include <stdarg.h>
#include <stdnoreturn.h>
#include <stdint.h>
#include <signal.h>

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

volatile long long nb_recus ;
volatile sig_atomic_t recu_sigusr2 ;

void handler_fils (int signo)
{
    switch (signo)
    {
	case SIGUSR1 :
	    nb_recus++ ;
	    break ;

	case SIGUSR2 :
	    recu_sigusr2 = 1 ;
	    break ;

	default :
	    raler (0, "recu signal %d inconnu", signo) ;
    }
}

void fils (void)
{
    while (! recu_sigusr2)
    {
	/* rien => attente active */
	pause () ;
    }
    printf ("fils : j'ai reçu %lld SIGUSR1\n", nb_recus) ;
}

volatile sig_atomic_t recu_sigalrm ;

void handler_pere (int signo)
{
    (void) signo ;
    recu_sigalrm = 1 ;
}

int main (int argc, const char *argv [])
{
    struct sigaction s ;
    pid_t pid_fils ;
    long long int nb_envoyes ;
    int nsec, raison ;

    if (argc != 2)
	raler (0, "usage: sig nb-secondes") ;
    nsec = atoi (argv [1]) ;

    // préparer l'arrivée de SIGUSR1 avant le démarrage du fils
    // pour que le fils en hérite
    s.sa_handler = handler_fils ;
    s.sa_flags = 0 ;
    CHK (sigemptyset (&s.sa_mask)) ;
    CHK (sigaction (SIGUSR1, &s, NULL)) ;

    // préparer l'arrivée de SIGUSR2 pour héritage par le fils
    CHK (sigaction (SIGUSR2, &s, NULL)) ;

    nb_recus = 0 ;	// initialisation dans le père pour héritage ds le fils
    recu_sigusr2 = 0 ;	// idem


    switch (pid_fils = fork ())
    {
	case -1 :
	    raler (1, "cannot fork") ;

	case 0 :
	    fils () ;
	    exit (0) ;
	default :
	    break ;
    }

    // préparer l'arrivée de SIGALRM
    recu_sigalrm = 0 ;
    s.sa_handler = handler_pere ;
    s.sa_flags = 0 ;
    CHK (sigemptyset (&s.sa_mask)) ;
    CHK (sigaction (SIGALRM, &s, NULL)) ;

    // déclencher la minuterie pour le nombre de secondes passé en argument
    alarm (nsec) ;

    nb_envoyes = 0 ;
    while (! recu_sigalrm)
    {
	CHK (kill (pid_fils, SIGUSR1)) ;
	nb_envoyes++ ;
    }

    CHK (kill (pid_fils, SIGUSR2)) ;
    printf ("père : j'ai envoyé %lld SIGUSR1 au fils\n", nb_envoyes) ;

    CHK (wait (&raison)) ;
    // vérifier scrupuleusement la raison de la terminaison du fils
    if (WIFSIGNALED (raison))
	raler (0, "fils terminé par signal %d\n", WTERMSIG (raison)) ;
    if (WIFEXITED (raison))
    {
	if (WEXITSTATUS (raison) != 0)
	    raler (0, "fils terminé par exit %d\n", WEXITSTATUS (raison)) ;
    }
    else raler (0, "fils terminé pour raison indéterminée") ;

    exit (0) ;
}
