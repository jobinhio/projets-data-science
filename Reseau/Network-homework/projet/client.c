#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <stdnoreturn.h>
#include <stdarg.h>
#include <dirent.h>
#include <libgen.h>
#include <fcntl.h>
#include <sys/stat.h>

// #define BUFFER_SIZE 1048576
// #define	MAXLEN	1024
#define MAXLEN	1048576
// #define	SERVICE	"9000"		    /* ou un nom dans /etc/services */
#define MAX_ADRESSE 100         /* taille max d'une adresse IPv4 ou IPv6 ou 
                                   nom DNS */
#define MAX_PORT 10             /* taille max d'un numéro de port TCP ou UDP */
#define NOM_FICHIER_CONFIG "adserv.conf"
#define MAX_STR_FORMAT 50      /* taille max d'une chaîne de format */
#define NB_SERVEURS 2
#define CHEMIN_MAX 128

#define	CHK(op)		do { if ((op) == -1) raler (1, #op) ; } while (0)
#define	CHKN(op)	do { if ((op) == NULL) raler (1, #op) ; } while (0)

struct serveur {
    char adresse [MAX_ADRESSE] ;
    char port [MAX_PORT] ;
} ;

enum socketType {TCP, UDP} ;

// usage pour pouvoir debugger
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

int estValide (int argc, char *argv [])
{
    int ok;

    if (argc < 3)
        ok = 0 ;
    else if (strcmp(argv[1], "image") == 0)
    {
        if (argc == 3)
            ok = strcmp(argv[2], "list") == 0;
        else if (argc == 4)
        {
            ok = strcmp(argv[2], "add") == 0 || 
                 strcmp(argv[2], "del") == 0 || 
                 strcmp(argv[2], "get") == 0 ||
                 strcmp(argv[2], "test") == 0;
        }
        else
            ok = 0 ;
    }
    else if (strcmp(argv[1], "tag") == 0)
    {
        if (argc >= 4 && strcmp(argv[2], "image"))
            ok = 1;
        else if (argc == 5)
            ok = strcmp(argv[2], "add") == 0 || 
                 strcmp(argv[2], "del") == 0;
    }
    else
        ok = 0 ;

    return ok;
}

void usage (char *argv0)
{
    char *msg = "usage: %s image list\n"
                "usage: %s image test image\n"
                "usage: %s image add image\n"
                "usage: %s image del image\n"
                "usage: %s image tag image \n"
                "usage: %s image get image\n"
                "usage: %s tag add image tag\n"
                "usage: %s tag del image tag\n"
                "usage: %s tag image tag ... tag\n";
    raler (0, msg, argv0, argv0, argv0, argv0, argv0, argv0, argv0, argv0) ;
}

// à améliorer : la structure du fichier doit être vérifiée 
void lireConfigServeur (struct serveur *serveurs)
{
    int n;
    char format [MAX_STR_FORMAT] ;
    FILE *f = NULL ;

    n = snprintf (format, MAX_STR_FORMAT, " %%%d[^,], %%%ds", 
            MAX_ADRESSE - 1, MAX_PORT - 1) ;
    if (n < 0)
        raler (0, "snprintf") ;

    CHKN (f = fopen (NOM_FICHIER_CONFIG, "r")) ;
    for (int i = 0 ; i < NB_SERVEURS ; i++)
    {
        n = fscanf (f, format, serveurs [i].adresse, serveurs [i].port) ;
        if (n != 2)
            raler (0, "fscanf") ;
        // traiter cas n == EOF
    }

    if (fclose (f) == EOF)
        raler (0, "fclose") ;
}

int preparerSocket (const char *host, const char *serv, enum socketType type)
{
    struct addrinfo hints, *res, *res0 ;
    int s, r ;
    char *cause ;

    memset (&hints, 0, sizeof hints) ;
    hints.ai_family = PF_UNSPEC ;
    hints.ai_socktype = (type == TCP) ? SOCK_STREAM : SOCK_DGRAM ;
    r = getaddrinfo (host, serv,  &hints, &res0) ;
    if (r != 0)
        raler (1, "getaddrinfo: %s\n", gai_strerror (r)) ;

    s = -1 ;
    for (res = res0 ; res != NULL ; res = res->ai_next)
    {
        s = socket (res->ai_family, res->ai_socktype, res->ai_protocol) ;
        if (s == -1)
            cause = "socket" ;
        else if (type == TCP)
        {
            r = connect (s, res->ai_addr, res->ai_addrlen) ;
            if (r == -1)
            {
                cause = "connect" ;
                close (s) ;
                s = -1 ;
            }
            else 
                break ;
        }
    }
    if (s == -1) raler (1, cause) ;
    freeaddrinfo (res0) ;

    return s;
}

void reqListeImages(int s, char *buf)
{
    char typeReq = 0;

    // doit d'abord envoyer une requête au serveur
    CHK (write (s, &typeReq, 1)) ;
    // puis recevoir la réponse
    CHK (read (s, buf, MAXLEN)) ;
}

// s = preparerSocket (serveurs [0].adresse, serveurs [0].port, TCP) ;
// reqTesterExistenceImage(s, argv[3], buf);
// if (buf[0] == 1) // octet nul
//     printf("L'image existe\n");
// else
// {
//     printf("L'image n'existe pas\n");
//     printf("%s\n", &buf[1]);
// }
// close (s) ;
void reqTesterExistenceImage(int s, const char *nom, char *buf)
{
    int r;
    char typeReq = 1;
    char lgNom = strlen(nom) + 1; // +1 pour le caractère '\0'
    char bufReq[MAXLEN];
    
    bufReq[0] = typeReq;
    bufReq[1] = lgNom;
    memcpy(&bufReq[2], nom, lgNom);

    // doit d'abord envoyer une requête au serveur
    CHK (write (s, bufReq, lgNom + 2)) ;
    // puis recevoir la réponse
    CHK (r = read (s, buf, MAXLEN)) ;
}

// nom est le nom du fichier (basename)
void reqEnvoyerImage(int s, char *nom, char *bufRec)
{
    char *nomBase;
    char bufEnv [MAXLEN];
    char typeReq = 2;
    uint32_t taille;
    int fd;
    struct stat stbuf;

    // doit d'abord envoyer une requête au serveur
    bufEnv[0] = typeReq;
    CHKN (nomBase = basename(nom));
    bufEnv[1] = strlen(nomBase) + 1; // longueur du nom + caractère nul
    memcpy(&bufEnv[2], nomBase, strlen(nomBase) + 1);
    CHK (lstat (nom, &stbuf)) ;
    taille = htonl (stbuf.st_size) ;
    memcpy (&bufEnv[2 + strlen(nomBase) + 1], &taille, sizeof taille) ;
    // lire le contenu du fichier et l'ajouter à bufEnv
    printf("requete: %d\n", bufEnv[0]);
    CHK (fd = open (nom, O_RDONLY)) ;
    CHK (read (fd, &bufEnv[2 + strlen(nomBase) + 1 + sizeof taille], 
            stbuf.st_size)) ;
    CHK (close (fd)) ;
    CHK (write (s, bufEnv, 2 + strlen(nomBase) + 1 + sizeof taille + 
            stbuf.st_size)) ;
    // puis recevoir la réponse
    CHK (read (s, bufRec, MAXLEN)) ;
}

void reqRecupImage(int s, char *nom, char *bufRec)
{
    char *nomBase;
    char bufEnv [MAXLEN];
    char typeReq = 3;

    // doit d'abord envoyer une requête au serveur
    bufEnv[0] = typeReq;
    CHKN (nomBase = basename(nom));
    bufEnv[1] = strlen(nomBase) + 1; // longueur du nom + caractère nul
    memcpy(&bufEnv[2], nomBase, strlen(nomBase) + 1);
    CHK (write (s, bufEnv, 2 + strlen(nomBase) + 1)) ;
    // puis recevoir la réponse
    CHK (read (s, bufRec, MAXLEN)) ;
}

void reqSupImage(int s, char *nom, char *bufRec)
{
    char *nomBase;
    char bufEnv [MAXLEN];
    char typeReq = 4;

    // doit d'abord envoyer une requête au serveur
    bufEnv[0] = typeReq;
    CHKN (nomBase = basename(nom));
    bufEnv[1] = strlen(nomBase) + 1; // longueur du nom + caractère nul
    memcpy(&bufEnv[2], nomBase, strlen(nomBase) + 1);
    CHK (write (s, bufEnv, 2 + strlen(nomBase) + 1)) ;
    // puis recevoir la réponse
    CHK (read (s, bufRec, MAXLEN)) ;
}

int main (int argc, char *argv [])
{
    int s;
    uint16_t nbNoms;
    uint32_t taille;
    char buf [MAXLEN] ;
    struct serveur serveurs [NB_SERVEURS] ; /*indice 0 : serveur image, 
                                            indice 1 : serveur tag*/
                

    if (!estValide(argc, argv))
        usage(argv[0]);

    lireConfigServeur (serveurs) ;

    if (strcmp(argv[1], "image") == 0)
    {
        if (strcmp(argv[2], "list") == 0)
        {
            s = preparerSocket (serveurs [0].adresse, serveurs [0].port, TCP) ;
            reqListeImages(s, buf);
            // on extrait le nombre d'images de buf
            memcpy(&nbNoms, buf, sizeof nbNoms);
            nbNoms = ntohs (nbNoms) ;
            printf("Nombre d'images: %d\n", nbNoms);
            printf("%s\n", &buf[sizeof nbNoms]);
            close (s) ;
        }
        else if (strcmp(argv[2], "test") == 0)
        {
            s = preparerSocket (serveurs [0].adresse, serveurs [0].port, TCP) ;
            reqTesterExistenceImage(s, argv[3], buf);
            if (buf[0] == 1) // octet nul
                printf("L'image existe\n");
            else
            {
                printf("L'image n'existe pas\n");
                printf("%s\n", &buf[1]);
            }
        }
        else if (strcmp(argv[2], "add") == 0)
        {
            s = preparerSocket (serveurs [0].adresse, serveurs [0].port, TCP) ;
            reqEnvoyerImage(s, argv[3], buf);
            if (buf[0] == 1)
                printf("L'image a été ajoutée\n");
            else
                printf("L'image n'a pas été ajoutée\n");
            close (s) ;
        }
        else if (strcmp(argv[2], "del") == 0)
        {
            s = preparerSocket (serveurs [0].adresse, serveurs [0].port, TCP) ;
            reqSupImage(s, argv[3], buf);
            if (buf[0] == 1)
                printf("L'image a été supprimée\n");
            else
                printf("L'image n'a pas été supprimée\n");
        }
        else // forcément "get"
        {
            s = preparerSocket (serveurs [0].adresse, serveurs [0].port, TCP) ;
            reqRecupImage(s, argv[3], buf);
            // en supposant que l'image existe
            // on extrait la taille de l'image de buf
            memcpy(&taille, buf, sizeof taille);
            taille = ntohl (taille) ;
            // on écrit le contenu de l'image sur la sortie standard
            CHK (write (1, &buf[sizeof taille], taille)) ;
            close (s) ;
        }
    }
    else // forcément "tag"
    {
        if (strcmp(argv[2], "add") == 0)
        {}
        else if (strcmp(argv[2], "del") == 0)
        {}
        else // forcément "image"
        {}
    }

    // while ((r = read (0, buf, MAXLEN)) > 0)
	//     write (s, buf, r) ;
    // close (s) ;

    exit (0) ;
}
