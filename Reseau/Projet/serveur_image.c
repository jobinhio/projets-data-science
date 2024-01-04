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
void RepSendImageToServer(int clientSocket,char *requete, char *rep)
{

    char reponse [MAXLEN];
    char nchemin [CHEMIN_MAX + 1];
    uint32_t tailleContenu;
    int n, fd;


    //recuperation de tailleNom
    char tailleNom = requete[0]; 
    char nom [(int) tailleNom]; // nom de l'image + caractère nul

    
    //Nom fichier
    memcpy(nom, &requete[1], tailleNom);

    //TailleContenu
    memcpy(&tailleContenu, &requete[tailleNom +1], sizeof tailleContenu);
    tailleContenu = ntohl (tailleContenu) ;

    // Ecriture dans la base de données
    n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, nom) ;
    if (n < 0 || n > CHEMIN_MAX)
        raler(0, "chemin '%s/%s' trop long", rep, nom) ;
    CHK (fd = open (nchemin, O_WRONLY | O_CREAT, 0666)) ;
    CHK (write (fd, &requete[tailleNom + 1 + sizeof tailleContenu], tailleContenu)) ;
    CHK (close (fd)) ;

    // envoyer la réponse au client
    reponse[0] = 1; // longueur du message d'erreur (pas d'erreur)
    reponse[1] = 0; // caractère nul
    CHK (write (clientSocket, reponse, 2)) ;

}



void RepListeImages (const int in, char *rep)
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

void RepTesterExistenceImage(int clientSocket,char *requete, char *rep)
{
    struct stat stbuf ;
    char nchemin [CHEMIN_MAX + 1];
    char tailleNom = requete[0]; // longueur du nom de l'image
    char nom [tailleNom]; // nom de l'image + caractère nul
    char *msg = "image inexistante"; // message à envoyer au client
    int n, existe = 0;
    char bufEnv [MAXLEN];

    memcpy(nom, &requete[1], tailleNom);

    // tester l'existence de l'image
    n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, nom) ;
    if (n < 0 || n > CHEMIN_MAX)
        raler(0, "chemin '%s/%s' trop long", rep, nom) ;
    
 

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

    CHK (write (clientSocket, bufEnv, strlen(msg) + 2)) ;
}


void RepSupImage(int s, char *bufRec, char *rep)
{
    char tailleNom = bufRec[0]; // longueur du nom de l'image
    char nom [(int) tailleNom]; // nom de l'image + caractère nul
    char nchemin [CHEMIN_MAX + 1];
    int n;
    char bufEnv [MAXLEN];

    memcpy(nom, &bufRec[1], tailleNom);

    n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, nom) ;
    if (n < 0 || n > CHEMIN_MAX)
        raler(0, "chemin '%s/%s' trop long", rep, nom) ;
    CHK (unlink (nchemin)) ;

    // envoyer la réponse au client
    bufEnv[0] = 1; // longueur du message d'erreur (pas d'erreur)
    bufEnv[1] = 0; // caractère nul
    CHK (write (s, bufEnv, 2)) ;
    printf ("image supprimée\n");
}




void RepRecupImage(int s, char *bufRec, char *rep)
{
    char tailleNom = bufRec[0]; // longueur du nom de l'image
    char bufEnv [MAXLEN];
    char nom [(int) tailleNom]; // nom de l'image + caractère nul
    char nchemin [CHEMIN_MAX + 1];
    int n, fd;
    struct stat stbuf;


    memcpy(nom, &bufRec[1], tailleNom);

    n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, nom) ;
    if (n < 0 || n > CHEMIN_MAX)
        raler(0, "chemin '%s/%s' trop long", rep, nom) ;

    CHK (lstat (nchemin, &stbuf)) ;
    uint32_t taille = htonl (stbuf.st_size) ;
    memcpy (bufEnv, &taille, sizeof taille) ;



    CHK (fd = open (nchemin, O_RDONLY)) ;
    // CHK (read (fd, &bufEnv[sizeof taille], stbuf.st_size)) ;

    printf ("taille = %u\n",taille) ;
    printf ("taillestbuf = %lu\n", stbuf.st_size) ;
    printf ("sizeof taille = %lu\n", sizeof taille) ;




    if( stbuf.st_size > (MAXLEN-(sizeof taille)) )
        raler(0,"taille:%ld",stbuf.st_size);

    ssize_t nlus;
    CHK (nlus = read (fd, &bufEnv[sizeof taille], stbuf.st_size)) ;
    CHK (close (fd)) ;


    printf ("nlus = %lu\n", nlus) ;


    if( nlus != (ssize_t) stbuf.st_size )
        raler(0,"nlus :%ld",stbuf.st_size);

    CHK (write (s, bufEnv, sizeof taille + nlus)) ;


    printf ("image envoyée\n") ;

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
        case 0: // Reponse à lister les images présentes
            printf("type : %d\n", type);
            RepListeImages (clientSocket,rep);
            break;
        case 1: // Reponse à tester l’existence d’une image
            printf("type : %d\n", type);
            RepTesterExistenceImage(clientSocket,&requete[1],rep);
            break;
        case 2: // Reponse à envoyer une image vers le serveur
            printf("type : %d\n", type);
            RepSendImageToServer(clientSocket,&requete[1],rep);
            break;
        case 3: // Reponse à récupérer une image depuis le serveur 
            // printf("type : %d\n", type);
            RepRecupImage(clientSocket,&requete[1],rep);


            break;
        case 4: // Reponse à supprimer une image sur le serveur
            printf("type : %d\n", type);
            RepSupImage(clientSocket,&requete[1],rep);
            break;
        default:
            printf("erreur \n");
        break;
    }

    
}

/*

void serveur ( int clientSocket,char *rep)
{

    // reception des requetes


    
    // // pour le type de requete recu
    // char requete [MAXLEN] ;
    // CHK (read (in, &requete, MAXLEN));


    // char reponse [MAXLEN];
    // char nchemin [CHEMIN_MAX + 1];
    // int n, fd;
    // struct stat stbuf;
    // uint32_t taille;

    // char type = requete[0];
    // char tailleNom = requete[1]; // longueur du nom de l'image
    // char nom [(int) tailleNom]; // nom de l'image + caractère nul

    


    // lecture entiere du la requete du client
    char requete [MAXLEN] ;
    CHK (read (clientSocket, &requete, MAXLEN));


    char reponse [MAXLEN];
    char nchemin [CHEMIN_MAX + 1];
    uint32_t tailleContenu;
    int n, fd;

    // recuperation du type
    char type = requete[0];
    //recuperation de tailleNom
    char tailleNom = requete[1]; 
    char nom [(int) tailleNom]; // nom de l'image + caractère nul


    switch (type)
    {
        case 0: // lister les images présentes
            printf("type : %d\n", type);
            break;
    
        case 1: // tester l’existence d’une image
            printf("type : %d\n", type);
            break;
        case 2: // envoyer une image vers le serveur

            //Nom fichier
            memcpy(nom, &requete[2], tailleNom);

            //TailleContenu
            memcpy(&tailleContenu, &requete[tailleNom +2], sizeof tailleContenu);
            tailleContenu = ntohl (tailleContenu) ;

            // Ecriture dans la base de données
            n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, nom) ;
            if (n < 0 || n > CHEMIN_MAX)
                raler(0, "chemin '%s/%s' trop long", rep, nom) ;
            CHK (fd = open (nchemin, O_WRONLY | O_CREAT, 0666)) ;
            CHK (write (fd, &requete[tailleNom + 2 + sizeof tailleContenu], tailleContenu)) ;
            CHK (close (fd)) ;

            // envoyer la réponse au client
            reponse[0] = 1; // longueur du message d'erreur (pas d'erreur)
            reponse[1] = 0; // caractère nul
            CHK (write (clientSocket, reponse, 2)) ;

            break;
        case 3: // récupérer une image depuis le serveur 
            printf("type : %d\n", type);
            break;
        case 4: // supprimer une image sur le serveur
            printf("type : %d\n", type);
            break;
        default:
            printf("erreur \n");
        break;
    }

    
}
*/


void Connexion(const char *serv_adrIPv4, int serv_port, int socketType,char *rep)
{
    int serverSocket;
    struct sockaddr_in serv_addr;

    // Création du socket serveur
    CHK(serverSocket = socket(AF_INET, socketType, 0));

    // Configurer l'adresse du serveur
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY; //inet_addr(IMAGE_IPV4);
    serv_addr.sin_port = htons(IMAGE_PORT);

    // Lier la socket à l'adresse et au port
    int r;
    r = bind(serverSocket, (struct sockaddr *)&serv_addr, sizeof serv_addr);
    if (r == -1) raler (0,"bind") ;

    // Mettre la socket en mode écoute
    r = listen(serverSocket, 5);
    if (r == -1) raler (0,"listen") ;

    printf("Le serveur écoute sur le port %d...\n", IMAGE_PORT);

    // Accepter les connexions entrantes
    int clientSocket;
    struct sockaddr_in clientAddr;
    socklen_t clientAddrLen = sizeof(clientAddr);

    r = (clientSocket = accept(serverSocket, (struct sockaddr *)&clientAddr, &clientAddrLen)) ;
    if (r == -1) raler (0,"accept") ;

    printf("Connexion acceptée depuis %s:%d\n", inet_ntoa(clientAddr.sin_addr), ntohs(clientAddr.sin_port));

    // Ici, vous pouvez interagir avec le client en utilisant clientSocket

    serveur ( clientSocket,rep);

    // Fermer les sockets
    close(clientSocket);
    close(serverSocket);

}


   /*
    // Boucle principale d'acceptation des connexions
    int clientSocket;
    struct sockaddr_in client_adr;
    socklen_t client_adrLen = sizeof(client_adr);
    for (;;) 
    {
        client_adrLen  = sizeof client_adr;
        clientSocket = accept(serverSocket, (struct sockaddr *)&client_adr, &client_adrLen );
        printf("client accepté\n");
        serveur(clientSocket);
        close(clientSocket);
    }
    // Fermeture du socket
    close(serverSocket);

    */

    

int main(int argc, char *argv[]) 
{

    //usage 
    if (argc != 3)
    {
        usage(argv[0]);
    }
    int image_port;
    image_port= atoi(argv[1]);
    char *RepImage = argv[2];


    // Ecriture dans InfoServeur
    WriteInfoServeur("image", IMAGE_IPV4, image_port);
    WriteInfoServeur("tag", TAG_IPV4,TAG_PORT);
    // WriteInfoServeur("image", IMAGE_IPV4, IMAGE_PORT);

    

    // Exemple d'utilisation pour un serveur TCP
    Connexion(IMAGE_IPV4, IMAGE_PORT, SOCK_STREAM,RepImage);


    return 0;
}