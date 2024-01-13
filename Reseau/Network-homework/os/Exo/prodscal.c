#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <errno.h>
#include <stdint.h>
#include <stdarg.h>
#include <stdnoreturn.h>

#include <time.h>

#define	CHK(op)		do { if ((op) == -1) raler (1, #op) ; } while (0)
#define	CHKN(op)	do { if ((op) == NULL) raler (1, #op) ; } while (0)

#define MAX_UNIT 9 
#define MAX_CHEMIN 1024

#define MAX_NUMBER 1000000000


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


char *creer_chemin(int numfile)
{
    static char chemin [MAX_CHEMIN];
    int len;

    len = snprintf(chemin, sizeof chemin, "res%d", numfile);  
    if( len == -1 || len >= (int) sizeof chemin)
        raler(0,"chemin trop long");
    return chemin;
}


void fils (int numfile,unsigned int delai, const char *xi, const char *yi)
{
    char *chemin;
    int fd;
    unsigned int t;

    // création des fichier  et redirection de stdout vers res_i
    chemin = creer_chemin (numfile);
    CHK (fd = open ( chemin, O_WRONLY | O_CREAT | O_TRUNC, 0666));
    CHK(dup2(fd, 1));
    CHK(close (fd));

    // attente aléatoire  
    srand(time(NULL));
    if ( delai != 0)    
        t = rand() % (delai + 1);
    else
        t = 0;

    __useconds_t nb_second = (__useconds_t)t*1000;
    usleep(nb_second);

    execlp("expr", "expr", xi, "*", yi, NULL);
    raler(1," échec expr ");
}


void papa(int n)
{
    int fd,len;
    char *chemin,*tab[2*n+1] ;
    ssize_t nlus ;
    long int nombre;

    for (int i = 0; i < n; i++)
    {
        char *buffer;
        CHKN(buffer = (char*) malloc((2*MAX_UNIT +1) * sizeof(char)));

        // lecture des fichier res_i
        chemin = creer_chemin (i);
        CHK (fd = open ( chemin, O_RDONLY ));
        CHK(nlus = read (fd, buffer, 2*MAX_UNIT ));
        CHK(close (fd));  

        // verifaction 
        if( nlus == 2*MAX_UNIT+1)
            raler(0,"nombre trop grands dans %s\n",chemin);
        buffer[nlus] = '\0'; 

        // verification intermédiaire
        nombre = atol(buffer);
        if(nombre >= MAX_NUMBER )
            raler(0,"valeur fournie trop grande\n");

        len = snprintf(buffer, 2*MAX_UNIT+1, "%ld", nombre);  
        if( len == -1 || len >= (int) 2*MAX_UNIT+1)
            raler(0,"chemin trop long\n");

        tab[ 2*i+1] = buffer;
        tab[2*i] = "+";
        // suppression fichier res_i
        CHK (unlink (chemin)); 
    }

    tab[0] = "expr";
    tab[2*n] = NULL;

    execvp("expr",tab);
    raler(1," échec expr ");
}




int main (int argc, const char *argv [])
{
    int n ;
    pid_t pidfils ;
    int raison;
    unsigned int long delai ;


    if ( argc % 2 != 0 || argc <= 2  )
	    raler (0, "usage: %s délai x1 ... xn y1 ... yn", argv [0]) ;
    
    delai = atol(argv [1]) ;
    if ( (int) delai < 0)
	    raler (0, "delai est invalide") ;

    // créer n processus fils
    n = (argc - 2 )/2 ; 
    for (int i = 0 ; i < n ; i++)
    {
        switch (fork ())
        {
            case -1 :
                raler (1, "fork fils numéro %d", i) ;
                break;

            case 0 : // fils
                fils(i, delai ,argv [ 2 + i], argv [ 2 + n + i]);
            default : 
                break ;
        }
    }

    // attendre la terminaison des n fils
    for (int i = 0 ; i < n ; i++)
    {
        CHK (pidfils = wait (&raison)) ;
        if (! (WIFEXITED (raison) && WEXITSTATUS (raison) == 0))
            raler (0, "fils pid =%jd terminé anormalement",(intmax_t) pidfils) ;
    }

    // qd tous les fils se sont terminés la partie du père
    papa (n);
    exit(0);
}
