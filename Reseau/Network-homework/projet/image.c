#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <syslog.h>
#include <limits.h>
#include <stdnoreturn.h>
#include <stdarg.h>
#include <dirent.h>
#include <fcntl.h>

// #define	MAXLEN	1024
#define MAXLEN	1048576
#define	SERVICE	"9000"		/* ou un nom dans /etc/services */
#define	MAXSOCK	32
#define CHEMIN_MAX 128

#define	CHK(op)		do { if ((op) == -1) raler_log (1, #op) ; } while (0)
#define	CHKN(op)	do { if ((op) == NULL) raler_log (1, #op) ; } while (0)

// à utiliser en production
// void raler_log (char *msg)
// {
//     syslog (LOG_ERR, "%s: %m", msg) ;
//     exit (1) ;
// }

// usage pour pouvoir debugger
noreturn void raler_log (int syserr, const char *fmt, ...)
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

void usage (char *argv0)
{
    raler_log (0, "usage: %s [port] repertoire\n", argv0) ;
}

// explore le répertoire indiquée par rep et prépare le contenu à envoyer
// à changer pour faire simple :
// - utiliser un buffer MAXLEN
// - envoyer le contenu du buffer à chaque fois qu'il est plein
// - éviter les realloc
void reqListeImages (const int in, char *rep)
{
    struct stat stbuf ;
    DIR *dp ;
    struct dirent *d ;
    uint16_t nbNoms = 0;
    int nbOctets = 2;
    int ind;
    char *buf = NULL;
    int n;
    char nchemin [CHEMIN_MAX + 1];

    CHKN (buf = (char *) realloc (buf, nbOctets)) ;

    CHKN (dp = opendir (rep)) ;
    while ((d = readdir (dp)) != NULL)
    {
        if (strcmp (d->d_name, ".") != 0 && strcmp (d->d_name, "..") != 0)
        {
            n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, d->d_name) ;
            if (n < 0 || n > CHEMIN_MAX)
                raler_log (0, "chemin '%s/%s' trop long", rep, d->d_name) ;

            CHK (lstat (nchemin, &stbuf)) ;
            switch (stbuf.st_mode & S_IFMT)
            {
            case S_IFREG :
                nbNoms++;
                ind = nbOctets;
                nbOctets += strlen(d->d_name) + 1;
                CHKN (buf = (char *) realloc (buf, nbOctets)) ;
                n = snprintf(buf + ind, strlen(d->d_name) + 1, "%s", d->d_name);
                if (n < 0)
                    raler_log (0, "snprintf") ;
                buf[nbOctets - 1] = '\n';
                break ;

            default :
                // ignorer les autres types de fichiers
                break ;
            }
        }
    }
    CHK (closedir (dp)) ;

    if (nbOctets == 2) // pas d'images dans le répertoire
    {
        nbOctets += 1;
        CHKN (buf = (char *) realloc (buf, nbOctets)) ;
    }
    buf[nbOctets - 1] = 0; // octet de fin de chaîne

    // écrire les 2 octets indiquant le nombre d'images
    nbNoms = htons(nbNoms);
    memcpy(buf, &nbNoms, sizeof(nbNoms));
    CHK (write (in, buf, nbOctets)) ;

    free (buf) ;
}

void reqTesterExistenceImage(const int in, char *rep, const char *bufRec)
{
    struct stat stbuf ;
    char nchemin [CHEMIN_MAX + 1];
    char lgNom = bufRec[0]; // longueur du nom de l'image
    char nom [lgNom]; // nom de l'image + caractère nul
    char *msg = "image inexistante"; // message à envoyer au client
    int n, existe = 0;
    char bufEnv [MAXLEN];

    memcpy(nom, &bufRec[1], lgNom);

    // tester l'existence de l'image
    n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, nom) ;
    if (n < 0 || n > CHEMIN_MAX)
        raler_log (0, "chemin '%s/%s' trop long", rep, nom) ;
    CHK (lstat (nchemin, &stbuf)) ;
    switch (stbuf.st_mode & S_IFMT)
    {
    case S_IFREG :
        existe = 1;
        break ;

    default :
        // ignorer les autres types de fichiers
        break ;
    }
    
    bufEnv[0] = 1; // longueur du message d'erreur (pas d'erreur)
    bufEnv[1] = 0; // caractère nul
    if (!existe)
    {
        bufEnv[0] = strlen(msg) + 1; // longueur du message + caractère nul
        memcpy(&bufEnv[1], msg, strlen(msg) + 1);
    }

    CHK (write (in, bufEnv, strlen(msg) + 2)) ;
}

void reqEnvoyerImage(const int in, char *rep, const char *bufRec)
{
    char lgNom = bufRec[0]; // longueur du nom de l'image
    char bufEnv [MAXLEN];
    char nom [(int) lgNom]; // nom de l'image + caractère nul
    char nchemin [CHEMIN_MAX + 1];
    uint32_t taille;
    int n, fd;

    memcpy(nom, &bufRec[1], lgNom);
    memcpy(&taille, &bufRec[lgNom + 1], sizeof taille);
    taille = ntohl (taille) ;

    n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, nom) ;
    if (n < 0 || n > CHEMIN_MAX)
        raler_log (0, "chemin '%s/%s' trop long", rep, nom) ;
    CHK (fd = open (nchemin, O_WRONLY | O_CREAT, 0666)) ;
    CHK (write (fd, &bufRec[lgNom + 1 + sizeof taille], taille)) ;
    CHK (close (fd)) ;

    // envoyer la réponse au client
    bufEnv[0] = 1; // longueur du message d'erreur (pas d'erreur)
    bufEnv[1] = 0; // caractère nul
    CHK (write (in, bufEnv, 2)) ;
}

void reqRecupImage(int s, char *rep, char *bufRec)
{
    char lgNom = bufRec[0]; // longueur du nom de l'image
    char bufEnv [MAXLEN];
    char nom [(int) lgNom]; // nom de l'image + caractère nul
    char nchemin [CHEMIN_MAX + 1];
    int n, fd;
    struct stat stbuf;
    uint32_t taille;

    memcpy(nom, &bufRec[1], lgNom);

    n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, nom) ;
    if (n < 0 || n > CHEMIN_MAX)
        raler_log (0, "chemin '%s/%s' trop long", rep, nom) ;
    
    CHK (lstat (nchemin, &stbuf)) ;
    taille = htonl (stbuf.st_size) ;
    memcpy (bufEnv, &taille, sizeof taille) ;
    
    CHK (fd = open (nchemin, O_RDONLY)) ;
    CHK (read (fd, &bufEnv[sizeof taille], stbuf.st_size)) ;
    CHK (close (fd)) ;

    CHK (write (s, bufEnv, sizeof taille + stbuf.st_size)) ;
}

void reqSupImage(int s, char *rep, char *bufRec)
{
    char lgNom = bufRec[0]; // longueur du nom de l'image
    char nom [(int) lgNom]; // nom de l'image + caractère nul
    char nchemin [CHEMIN_MAX + 1];
    int n;
    char bufEnv [MAXLEN];

    memcpy(nom, &bufRec[1], lgNom);

    n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, nom) ;
    if (n < 0 || n > CHEMIN_MAX)
        raler_log (0, "chemin '%s/%s' trop long", rep, nom) ;
    CHK (unlink (nchemin)) ;

    // envoyer la réponse au client
    bufEnv[0] = 1; // longueur du message d'erreur (pas d'erreur)
    bufEnv[1] = 0; // caractère nul
    CHK (write (s, bufEnv, 2)) ;
}

void serveur (int in, struct sockaddr_storage sonadr, char *rep)
{
    int af ;
    char bufRec [MAXLEN] ;
    char padr[INET6_ADDRSTRLEN];
    void *nadr;
    // ssize_t r ;

    // while ((r = read (in, buf, MAXLEN)) > 0)
	// n += r ;
    // syslog (LOG_ERR, "nb d'octets lus = %d\n", n) ;

    af = ((struct sockaddr *) &sonadr)->sa_family ;
    switch (af)
    {
	case AF_INET :
	    nadr = & ((struct sockaddr_in *) &sonadr)->sin_addr ;
	    break ;
	case AF_INET6 :
	    nadr = & ((struct sockaddr_in6 *) &sonadr)->sin6_addr ;
	    break ;
    }
    CHKN (inet_ntop(af, nadr, padr, sizeof padr)) ;

    CHK (read (in, &bufRec, MAXLEN));
    switch (bufRec[0])
    {
    case 0: // lister les images présentes
        printf ("%s: demande la liste des images\n", padr) ;
        reqListeImages(in, rep);
        printf ("%s: liste envoyée\n", padr) ;
        break;
    case 1: // tester l'existence d'une image
        printf ("%s: demande de tester l'existence d'une image\n", padr) ;
        reqTesterExistenceImage(in, rep, &bufRec[1]);
        printf ("%s: réponse envoyée\n", padr) ;
        break;
    case 2: // envoyer une image vers le serveur
        printf ("%s: demande de reception d'une image\n", padr) ;
        reqEnvoyerImage(in, rep, &bufRec[1]);
        printf ("%s: image reçue\n", padr) ;
        break;
    case 3: // recupérer une image depuis le serveur
        printf ("%s: demande de récupération d'une image\n", padr) ;
        reqRecupImage(in, rep, &bufRec[1]);
        printf ("%s: image récupérée\n", padr) ;
        break;
    case 4: // supprimer une image sur le serveur
        printf ("%s: demande de suppression d'une image\n", padr) ;
        reqSupImage(in, rep, &bufRec[1]);
        printf ("%s: image supprimée\n", padr) ;
        break;
    default:
        printf ("%s: requête inconnue\n", padr) ;
        break;
    }
}

void demon (char *serv, char *rep)
{
    int s [MAXSOCK], sd, nsock, r, opt = 1 ;
    struct addrinfo hints, *res, *res0 ;
    char *cause ;

    memset (&hints, 0, sizeof hints) ;
    hints.ai_family = PF_UNSPEC ;
    hints.ai_socktype = SOCK_STREAM ;
    hints.ai_flags = AI_PASSIVE ;
    if ((r = getaddrinfo (NULL, serv,  &hints, &res0)) != 0) 
    {
        fprintf (stderr, "getaddrinfo: %s\n", gai_strerror (r)) ;
        exit (1) ;
    }

    nsock = 0 ;
    for (res = res0; res && nsock < MAXSOCK; res = res->ai_next) 
    {
        s [nsock] = socket (res->ai_family, res->ai_socktype, res->ai_protocol) ;
        if (s [nsock] == -1)
            cause = "socket" ;
        else 
        {
            setsockopt (s [nsock], IPPROTO_IPV6, IPV6_V6ONLY, &opt, sizeof opt) ;
            setsockopt (s [nsock], SOL_SOCKET, SO_REUSEADDR, &opt, sizeof opt) ;
            r = bind (s [nsock], res->ai_addr, res->ai_addrlen) ;
            if (r == -1) {
                cause = "bind" ;
                close (s [nsock]) ;
            } else {
                listen (s [nsock], 5) ;
                nsock++ ;
            }
        }
    }
    if (nsock == 0) raler_log (1, cause) ;
    freeaddrinfo (res0) ;

    for (;;) {
        fd_set readfds ;
        int i, max = 0 ;

        FD_ZERO (&readfds) ;
        for (i = 0 ; i < nsock ; i++) 
        {
            FD_SET (s [i], &readfds) ;
            if (s [i] > max)
            max = s [i] ;
        }
        CHK (select (max+1, &readfds, NULL, NULL, NULL));

        for (i = 0 ; i < nsock ; i++) 
        {
            struct sockaddr_storage sonadr ;
            socklen_t salong ;

            
            if (FD_ISSET (s [i], &readfds))
            {
                salong = sizeof sonadr ;
                sd = accept (s [i], (struct sockaddr *) &sonadr, &salong) ;
                if (fork () == 0) 
                {
                    serveur (sd, sonadr, rep) ;
                    exit (0) ;
                }
                close (sd) ;
            }
        }
    }
}

int main (int argc, char *argv [])
{
    char *serv, *rep ;
    char absrep[PATH_MAX];

    switch (argc) 
    {
    case 2 : 
        serv = SERVICE ; 
        rep = argv[1];
        break ;
    case 3 : 
        serv = argv [1] ; 
        rep = argv[2];
        break ;
	default : 
        usage (argv [0]) ; 
        break ;
    }

    CHKN (realpath (rep, absrep)) ;
    printf("repertoire = %s\n", absrep);

    // à utiliser en production
    // switch (fork ()) {
	// case -1 :
	//     perror ("cannot fork") ;
	//     exit (1) ;
	// case 0 :		/* le demon proprement dit */
	//     setsid () ; chdir ("/") ; umask (0) ;
	//     close (0) ; close (1) ; close (2) ;
	//     openlog ("exemple", LOG_PID | LOG_CONS, LOG_DAEMON) ;
	//     demon (serv) ;
	//     exit (1) ;
	// default :
	//     exit (0) ;
    // }

    // usage pour pouvoir debugger
    demon (serv, absrep) ;

    exit (0) ;
}
