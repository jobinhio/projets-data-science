#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <errno.h>
#include <stdarg.h>
#include <stdnoreturn.h>
#include <signal.h>

#define	CHK(op)		do { if ((op) == -1) raler (1, #op) ; } while (0)
#define	CHKN(op)	do { if ((op) == NULL) raler (1, #op) ; } while (0)

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

volatile sig_atomic_t recu_sigusr1, recu_sigusr2, recu_sigterm ;

// Même handler pour père et fils
void handler (int nosig)
{
    switch (nosig)
    {
	// signaux reçus par le fils
	case SIGUSR1 :
	    recu_sigusr1 = 1 ;
	    break ;
	case SIGUSR2 :
	    recu_sigusr2 = 1 ;
	    break ;
	// signaux reçus par le père
	case SIGTERM :		// ça aurait pu aussi être SIGUSR1 ou SIGUSR2
	    recu_sigterm = 1 ;
	    break ;
    }
}

// num : numéro du fils [0..n[
// fd : descripteur du fichier temporaire
void fils (int num, int fd)
{
    ssize_t nlus ;
    int vi ;
    sigset_t masque, vide ;
    pid_t pidpere ;

    // Pour minimiser le nombre d'appels à des primitives système :
    pidpere = getppid () ;

    // masque interdisant la prise en compte de SIGUSR1 et SIGUSR2
    CHK (sigemptyset (&masque)) ;
    CHK (sigaddset (&masque, SIGUSR1)) ;
    CHK (sigaddset (&masque, SIGUSR2)) ;

    // interdire la prise en compte de SIGUSR1 et SIGUSR2 pendant toute
    // la boucle, sauf au moment où on le décide
    CHK (sigprocmask (SIG_BLOCK, &masque, NULL)) ;

    // masque autorisant la prise en compte de tous les signaux
    CHK (sigemptyset (&vide)) ;

    while (! recu_sigusr2)
    {
	// attendre un signal SIGUSR1 ou SIGUSR2
	if (! recu_sigusr1 && ! recu_sigusr2)
	    (void) sigsuspend (&vide) ;	// attente autorisant SIGUSR1 et SIGUSR2

	if (recu_sigusr1)
	{
	    // lire la valeur reçue
	    recu_sigusr1 = 0 ;
	    CHK (lseek (fd, 0, SEEK_SET)) ;
	    CHK (nlus = read (fd, &vi, sizeof vi)) ;
	    if (nlus != sizeof vi)
		raler (0, "fils %d a lu %z octets", num, nlus) ;
	    printf ("fils %d affiche %d\n", num, vi) ;

	    // accuser réception auprès du père
	    CHK (kill (pidpere, SIGTERM)) ;
	}
    }

    // pour faire "propre", on remet le masque à la valeur initiale
    CHK (sigprocmask (SIG_UNBLOCK, &masque, NULL)) ;
}

// main
int main (int argc, char *argv [])
{
    int n, i, vi, fd, raison ;
    pid_t *pidfils ;
    char chemin [] = "/tmp/distrib.XXXXXX" ;
    struct sigaction s ;

    if (argc < 2)
	raler (0, "usage: distrib n v1 ... vn") ;
    n = atoi (argv [1]) ;
    if (n < 1)
	raler (0, "arg invalide") ;

    // Variable Length Array (VLA)
    // pid_t pidfils [n] ;

    CHKN (pidfils = calloc (n, sizeof (pid_t))) ;

    CHK (fd = mkstemp (chemin)) ;
    printf ("%s\n", chemin) ;
    CHK (unlink (chemin)) ;

    // Préparer l'arrivée des signaux avant que le premier processus
    // destinataire (un des fils) ne puisse le traiter
    s.sa_handler = handler ;
    s.sa_flags = 0 ;
    CHK (sigemptyset (&s.sa_mask)) ;
    CHK (sigaction (SIGUSR1, &s, NULL)) ;
    CHK (sigaction (SIGUSR2, &s, NULL)) ;
    CHK (sigaction (SIGTERM, &s, NULL)) ;

    // Création des processus fils
    for (i = 0 ; i < n ; i++)
    {
	switch (pidfils [i] = fork () )
	{
	    case -1 :
		raler (1, "fork fils %d", i) ;

	    case 0 :
		fils (i, fd) ;
		CHK (close (fd)) ;
		exit (0) ;

	    default :
		break ;
	}
    }

    // masque des signaux pour la section critique du père
    sigset_t masque, vide ;
    CHK (sigemptyset (&masque)) ;
    CHK (sigaddset (&masque, SIGTERM)) ;
    CHK (sigemptyset (&vide)) ;

    // Envoi des valeurs vi aux fils
    for (i = 2 ; i < argc ; i++)
    {
	vi = atoi (argv [i]) ;
	if (vi < 0)
	    raler (0, "v%d < 0", i-1) ;

	// envoyer la valeur
	CHK (lseek (fd, 0, SEEK_SET)) ;
	CHK (write(fd, &vi, sizeof vi)) ;

	// indiquer au fils (vi mod n) qu'il peut lire la valeur
	CHK (kill (pidfils [vi % n], SIGUSR1)) ;

	// attendre que le fils ait terminé la lecture
	CHK (sigprocmask (SIG_BLOCK, &masque, NULL)) ;
	if (! recu_sigterm)
	    (void) sigsuspend (&vide) ;
	recu_sigterm = 0 ;
	CHK (sigprocmask (SIG_UNBLOCK, &masque, NULL)) ;
    }

    CHK (close (fd)) ;

    // Indiquer aux fils de se terminer
    for (i = 0 ; i < n ; i++)
    {
	CHK (kill (pidfils [i], SIGUSR2)) ;
	CHK (wait (&raison)) ;
	if (WIFEXITED (raison))
	{
	    if (WEXITSTATUS (raison) != 0)
		raler (0, "fils %d terminé par exit != 0", i) ;
	}
	else if (WIFSIGNALED (raison))
	    raler (0, "fils %d terminé par sig = %d", i, WTERMSIG (raison)) ;
	else
	    raler (0, "fils %d terminé pour raison inconnue", i) ;
    }

    exit (0) ;
}
