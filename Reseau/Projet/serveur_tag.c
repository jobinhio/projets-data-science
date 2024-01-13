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

#define InfoServeur "InfoServeur.cfg"
#define IMAGE_IPV4 "127.0.0.1"
#define IMAGE_PORT 8080

#define TAG_IPV4 "127.0.0.1"
#define TAG_PORT 9090


#define	MAX_NOM_LEN 255 //  2^8 -1
#define	MAX_ERREUR_LEN 255 //  2^8 -1
#define	MAX_CONTENU_LEN  65535 //  2^16 -1






#define	CHEMIN_MAX	512
#define MAXLEN	2048576
#define MAX_ADDR_LEN 256

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

void usage (char *argv0)
{
    fprintf (stderr, "usage: %s port répertoire\n", argv0) ;
    exit (1) ;
}

void WriteInfoServeur(const char *serverName, const char *serv_adrIPv4, int serv_port)
{
    // Ouverture du fichier en mode écriture
    int fd;
    CHK(fd = open (InfoServeur, O_WRONLY | O_CREAT | O_APPEND, 0666));
    // Écriture des informations dans le fichier en utilisant write
    char buffer[MAX_ADDR_LEN + 50]; // Assez grand pour contenir les informations
    int necrit = snprintf(buffer, sizeof(buffer), "%s %s %d\n", serverName, serv_adrIPv4, serv_port);
    if (necrit < 0 || necrit >= sizeof(buffer))
        raler(0,"snprintf");

    buffer[necrit] ='\0';
    CHK(write(fd, buffer, necrit));
    // Fermeture du fichier
    CHK(close(fd));
}


char *base (char *chemin)
{
    char *p ;

    p = strrchr (chemin, '/') ;
    return p == NULL ? chemin : p+1 ;
}



/// Reponse

void RepListeTagOfImage(const int in, char *rep)
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
                raler(0, "chemin '%s/%s' trop long", rep, d->d_name) ;

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
                    raler (0, "snprintf") ;
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


void serveur ( int clientSocket,char *rep)
{
    // lecture entiere du la requete du client
    char requete [MAXLEN] ;
    CHK (read (clientSocket, &requete, MAXLEN));
    // recuperation du type
    char type = requete[0];

    switch (type)
    {
        case 0: // Reponse à lister les tags associés à une image
            printf("type : %d\n", type);
           RepListeTagOfImage(clientSocket,rep);
            break;
        default:
            printf("erreur \n");
        break;
    }

    
}


void Connexion(const char *serv_adrIPv4, int serv_port, int socketType, char *rep)
{
    int serverSocket;
    struct sockaddr_in serv_addr;

    // Create a UDP server socket
    CHK(serverSocket = socket(AF_INET, socketType, 0));

    // Configure the server address
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    serv_addr.sin_port = htons(serv_port);

    // Bind the socket to the address and port
    int r;
    r = bind(serverSocket, (struct sockaddr *)&serv_addr, sizeof(serv_addr));
    if (r == -1) raler(0, "bind");

    printf("Le serveur écoute sur le port %d...\n", serv_port);



    serveur(serverSocket, rep);

    // Close the socket
    close(serverSocket);
}



int main(int argc, char *argv[]) 
{

    //usage 
    if (argc != 3)
    {
        usage(argv[0]);
    }
    int tag_port;
    tag_port= atoi(argv[1]);
    char *RepImage = argv[2];


    // Ecriture dans InfoServeur pour communiquer au client
    WriteInfoServeur("tag", TAG_IPV4, tag_port);    

    // Exemple d'utilisation pour un serveur UDP
    Connexion(TAG_IPV4, tag_port, SOCK_DGRAM,RepImage);
    // Connexion(TAG_IPV4, TAG_PORT, SOCK_DGRAM,RepImage);


    return 0;
}