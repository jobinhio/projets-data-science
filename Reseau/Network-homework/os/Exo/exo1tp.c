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
#include <sys/wait.h>
#include <signal.h>

#define	CHK(op)		do { if ((op) == -1) raler (1, #op) ; } while (0)
#define	CHKN(op)	do { if ((op) == NULL) raler (1, #op) ; } while (0)


volatile sig_atomic_t signal_recu = 0 ;
volatile sig_atomic_t arret = 0 ;



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

void handler(int sig) 
{
    switch (sig)
    {
        case SIGUSR1:
            signal_recu = 0 ;
            break;
        
        case SIGUSR2:
            arret = 1;
            break;

        case SIGALRM :
            break;
    }

}




int main (int argc, const char *argv [])
{
    int nbsec = atoi(argv[1]);
    int count;
    pid_t pidfils;
    switch (fork())
    {
    case -1:
        raler(0, "fils mal cree");
        break;
    case 0:
        pidfils = getppid();

        while (!arret)
        {
            if(signal_recu)
                count++;
        }
        exit(0);

        break;
    default:
    while (1)
    {
        CHK(kill (pidpapa, SIGUSR1));

    }

    // envoie de 
    CHK(kill (pidpapa, SIGUSR2));

    
        break;
    }

}