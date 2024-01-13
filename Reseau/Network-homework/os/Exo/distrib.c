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

volatile sig_atomic_t recu_sigusr1 = 0, recu_sigusr2= 0, recu_alarm =0;


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



void handler_fils (int signo)
{
    switch (signo)
    {
	case SIGUSR1 :
	    recu_sigusr1 = 1 ;
	    break ;

	case SIGUSR2 :
	    recu_sigusr2 = 1 ;
	    break ;

	default :
	    raler (0, "recu signal %d inconnu", signo) ;
    }
}

void fils (int fd , int numproc, int pidpere)
{
    int vi;
    ssize_t nlus;

    sigset_t vide;

    // tout le code fils excecute en section critique
    sigset_t masque;
    sigemptyset(&masque) ;
    CHK(sigaddset(&masque, SIGUSR1));
    CHK(sigaddset(&masque, SIGUSR2));
    CHK(sigprocmask (SIG_BLOCK,&masque ,NULL)) ;

    while (1)
    {
        (void) sigsuspend(&vide);
        if(recu_sigusr1)
        {
            recu_sigusr1 = 0;
            CHK(nlus =read( fd, &vi,sizeof (int)));
            printf ("fils %d affiche %d\n", numproc, vi);

            // prevenir recu recu_sigusr1
            CHK(kill(pidpere, SIGALRM));
        }
        if(recu_sigusr2)
        {
            break;
        }
    }

    // USR2 est recu 
    CHK(close(fd));
    exit(0);
}


void handler_pere(int signum)
{
    switch (signum)
    {
        case SIGALRM :
            recu_alarm = 1 ;
            break ;

        default :
            raler (0, "recu signal %d inconnu", signum) ;
    }
}


void pere(int fd, int v[], pid_t pid_fils[] ,int p,int n)
{

    int id_proc;
    ssize_t necrit;

    sigset_t vide,masque;
    CHK(sigemptyset(&vide));

    // masquer SIGUSR2 pendant la durée du pere        
    CHK(sigemptyset(&masque));
    CHK(sigaddset(&masque, SIGALRM));
    CHK(sigprocmask(SIG_BLOCK, &masque, NULL));


    for (int i = 0; i < p; i++)
    {
        // ecire vi dans fichier
        int vi = v[i];
        CHK((necrit = write(fd,&vi,sizeof (int))));
        CHK(lseek(fd, -necrit, SEEK_CUR));

        id_proc = v[i]%n ;
        CHK(kill(pid_fils[id_proc], SIGUSR1));

        // attendre SIGALRM pour continuer
        CHK(sigemptyset(&vide));
        (void) sigsuspend(&vide);

        recu_alarm =0;
    }

    CHK(close(fd));

    // envoyer SIGUSR2 aux fils pour finir
    for (int i = 0; i < n; i++)
        CHK (kill (pid_fils[i], SIGUSR2));

}



int main (int argc, char *argv [])
{
    int i,fd, n,p, raison;
    struct sigaction sfils, spere  ;
    pid_t pid ;

    if (argc < 2)
	    raler (0, "usage : distrib n v1 ... vp") ;

    n = atoi(argv[1]);
    p = argc - 2;

    // nombre de processus correcte
    if (n <= 0)
	    raler (0, "nombre de processus invalide") ;

    // stockage des valeurs v
    int v[p];
    for (i = 0; i < p; i++)
    {
        v[i] = atoi(argv[i+2]);
        // pour avoir des valeurs positive 
        if (v[i] < 0)
	        raler (0, "vi doit être positif") ;
    }


    // creer et afficher fichier pour tous les fils
    char fichier[] = "/tmp/tempXXXXXX"; 
    CHK((fd = mkstemp(fichier)));
    printf("%s\n", fichier);

    // préparer l'arrivée de SIGUSR1 et de SIGUSR2 
    // pour que les fils 
    sfils.sa_handler = handler_fils ;
    sfils.sa_flags = 0 ;
    CHK (sigemptyset (&sfils.sa_mask)) ;
    CHK(sigaddset (& sfils.sa_mask , SIGALRM)) ;
    CHK (sigaction (SIGUSR1, &sfils, NULL)) ;
    CHK (sigaction (SIGUSR2, &sfils, NULL)) ;

    // préparer l'arrivée de SIGALRM 
    // pour le pere
    spere.sa_handler = handler_pere ;
    spere.sa_flags = 0 ;
    CHK (sigemptyset (&spere.sa_mask)) ;
    CHK(sigaddset (& spere.sa_mask , SIGUSR1)) ;
    CHK(sigaddset (& spere.sa_mask , SIGUSR2)) ;
    CHK (sigaction (SIGALRM, &spere, NULL)) ;

    // creation des fils 
    pid_t pid_fils[n] ;
    for (i = 0; i < n; i++)
    {
        switch (pid_fils[i] = fork ())
        {
        case -1 :
            raler (1, "cannot fork") ;

        case 0 :
            fils (fd,i,getppid()) ;
            exit (1) ;
        default :
            break ;
        }
    }

    pere(fd,v, pid_fils,p,n);

    // suppression fichier
    CHK(unlink(fichier));

    // attendre la terminaison des fils
    for (i = 0 ; i < n ; i++)
    {
        CHK (pid = wait (&raison)) ;
        // vérifier scrupuleusement la raison de la terminaison du fils
        if (WIFSIGNALED (raison))
        raler (0, "fils %jd terminé par signal %d\n", (intmax_t) pid, WTERMSIG (raison)) ;
        if (WIFEXITED (raison))
        {
        if (WEXITSTATUS (raison) != 0)
            raler (0, "fils %jd terminé par exit %d\n", (intmax_t) pid, WEXITSTATUS (raison)) ;
        }
        else raler (0, "fils %jd terminé pour raison indéterminée\n", (intmax_t) pid) ;
    }

    exit (0) ;
}
