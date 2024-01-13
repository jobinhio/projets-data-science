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

#define	CHK(op)		do { if ((op) == -1) raler (1, #op) ; } while (0)
#define	CHKN(op)	do { if ((op) == NULL) raler (1, #op) ; } while (0)

#define	CHEMIN_MAX	128 
#define	MARGE	1 
#define	BUF_MAX 1024


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


int compter_occurance(char *chemin,const  char *caractère)
{
    int count, fd, nlus;
    char buffer[BUF_MAX];

    count = 0;
    CHK((fd = open(chemin,O_RDONLY)));
    while ((nlus = read(fd,buffer,BUF_MAX)) > 0)
    {
        for (int i = 0; i < (int) nlus; i++)
            if (caractère[0] == buffer[i])
                count++;
    }

    CHK(nlus);
    CHK(close(fd));
    
    return count;

}


void fils(int fd_in, int fd_out,const  char *caractère, int numproc)
{
    char buffer[CHEMIN_MAX+MARGE]; 
    int occur, TAILLE, n;
    ssize_t nlus, nboctet_count, nboctet_numproc;

    // lecture du tube_entree 
    // on lit exactement CHEMIN_MAX+MARGE octet
    while( (nlus = read(fd_in, buffer, CHEMIN_MAX+MARGE)) >0)
    {
        char chemin[CHEMIN_MAX+2]; 
        if (nlus != CHEMIN_MAX+MARGE)
	        raler (0, "nlus est différent de  CHEMIN_MAX+MARGE") ;

        for (int j = 0; j < nlus; j++) 
        {
            if (buffer[j] != ' ') 
            {
                chemin[j] = buffer[j]; 
            }
            else
            {
                chemin[j] = '\0'; 
                if (strlen(chemin) > CHEMIN_MAX)
                    raler (0, "chemin trop grand\n") ;

                // verif que le chemin recuperer est correct
                struct stat stbuf ;
                CHK (lstat (chemin, &stbuf)) ;
                if (!((stbuf.st_mode & S_IFMT) == S_IFREG))
                    raler (0, "chemin donné incorrecte") ;
                break;
            }
        }        


        // compter le nb_occur
        occur = compter_occurance(chemin,caractère);
        nboctet_count  = sizeof(occur);
        nboctet_numproc  = sizeof(numproc);

        // ecrire tube_sortie  
        TAILLE = CHEMIN_MAX + (int)nboctet_count +(int)nboctet_numproc +3; // 3 = 2 ' '+ 1 \n
        char sortie[TAILLE];
        n = snprintf (sortie, sizeof sortie, "%s %d %d\n", chemin, occur, numproc) ; 
        if (n < 0 || n > TAILLE)
            raler (0, "sortie  trop long\n") ;

        CHK (write (fd_out, sortie, strlen(sortie))) ;
    }
    
    CHK(nlus);
}
    

void dernier_fils(int fd_in)
{
    char buffer[BUF_MAX];
    int nlus;

    while ((nlus = read(fd_in, buffer, BUF_MAX))  > 0)
    {
        for (int i = 0; i < (int) nlus; i++)
        {
            printf("%c",buffer[i]);
        }
    }

    CHK(nlus);
}


void fournir_file(const char *rep, int  fd_in)
{
    // parcourt le répertoire
    DIR *dp ;
    struct dirent *d ;
    char nch [CHEMIN_MAX+MARGE],info [CHEMIN_MAX+MARGE] ;	
    int n ;
    struct stat stbuf ;


    CHKN (dp = opendir (rep)) ;
    while ((d = readdir (dp)) != NULL)
    {
        if (strcmp (d->d_name, ".") != 0 && strcmp (d->d_name, "..") != 0)
        {
            n = snprintf (nch, CHEMIN_MAX+MARGE, "%s/%s", rep, d->d_name) ;    
            if (n < 0 || n > CHEMIN_MAX)
                raler (0, "chemin '%s/%s' trop long", rep, d->d_name) ;

            CHK (lstat (nch, &stbuf)) ;
            switch (stbuf.st_mode & S_IFMT)
            {
                case S_IFDIR :	// répertoire alors parcourir l'arborescence
                    fournir_file(nch, fd_in);
                    break ;
                case S_IFREG : // fichier régulier alors ecrire dans tube_entree
                    for (int i = 0; i < CHEMIN_MAX+MARGE; i++) 
                    {
                        if (i > (int) strlen(nch))
                        {
                            info[i] = ' ';
                        }
                        else
                        {
                            info[i] = nch[i];
                        }
                    }
                    info[CHEMIN_MAX+MARGE-1] = '\0';

                    // on ecrit exactement CHEMIN_MAX+MARGE octet
                    ssize_t necrit ;
                    CHK( (necrit = write(fd_in, info, CHEMIN_MAX+MARGE)) );
                    if (necrit != CHEMIN_MAX+MARGE)
	                    raler (0, "necrit est différent de  CHEMIN_MAX+MARGE") ;
                    break ;
                default :		// on fait rien ici
                    break ;
            }
        }
    }
    CHK (closedir (dp)) ;
}


int main (int argc, const char *argv [])
{   
    int tube_entre[2], tube_sortie[2],raison , nproc;
    const char *rep, *caractère ; 

    // vérification usage
    if ( argc != 4 )
	    raler (0, "usage : parcount répertoire caractère nproc") ;

    // récupération des arguments
    rep = argv[1];
    caractère = argv[2];
    nproc  = atoi(argv[3]);
    

    // pour avoir nproc > 0
    if ( nproc <= 0 )
	    raler (0, "nproc doit être strictement positif") ;

     // caractère inexistant ou trop long
    if ( strlen(caractère) != 1 )
	    raler (0, "il faut un caractère") ;


    //creer 2 tubes 
    CHK(pipe(tube_entre));
    CHK(pipe(tube_sortie));
    

    // création et opérations des nproc
    for (int i = 0; i < nproc; i++)
    {
        switch (fork ())
        {
            case -1 :
            raler (1, "erreur fork sur fils %d", i) ;
            break ;
            case 0 : //fils 
                // Fermeture des tubes
                CHK(close(tube_entre[1])); 
                CHK(close(tube_sortie[0])); 
                // part des fils
                fils(tube_entre[0], tube_sortie[1], caractère, i);
                // Fermeture des tubes
                CHK(close(tube_entre[0]));
                CHK(close(tube_sortie[1]));
                // terminaison du fils
                exit(0); 
            default :
            break ;
        }
    }


    //La création de ce processus permet de lire les données 
    // dans le bon ordre dans le tube de sortie
    // creer le dernier processus
    switch (fork ())
    {
        case -1 :
            raler (1, "erreur fork sur dernier fils") ;

        case 0 : //fils 
            // Fermeture des tubes
            CHK(close(tube_entre[1])); 
            CHK(close(tube_sortie[1]));
            CHK(close(tube_entre[0]));
            dernier_fils(tube_sortie[0]);
            // Fermeture tube 
            CHK(close(tube_sortie[0]));
            // Terminaison processus
            exit(0);

        default :
        break ;
    }

    // Fermeture lecture et ecriture tube_sortie côte père
    CHK(close(tube_sortie[0]));
    CHK(close(tube_sortie[1]));

    // Fermeture lecture tube_entree cote pere
    CHK(close(tube_entre[0]));
    // fournir les fichiers dans tube_entree 
    fournir_file(rep, tube_entre[1]);
    // Fermeture ecriture tube_entree cote pere
    CHK(close(tube_entre[1]));

    // attendre la terminaison des processus fils
    for (int i = 0 ; i < nproc+1 ; i++)
    {
        CHK (wait (&raison)) ;
        if (! (WIFEXITED (raison) && WEXITSTATUS (raison) == 0))
            raler (0, "un fils s'est mal terminé") ;
    }
    exit(0);

}