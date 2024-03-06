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


#define MAXADDRLEN 256
#define	CHEMIN_MAX	512
#define MAXLEN	3783406

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
    int fd;
    CHK(fd = open (InfoServeur, O_WRONLY | O_CREAT | O_APPEND, 0666));
    char buffer[MAXADDRLEN]; 
    int necrit = snprintf(buffer, MAXADDRLEN, "%s %s %d\n", serverName, serv_adrIPv4, serv_port);
    if (necrit < 0 || necrit >= MAXADDRLEN)
        raler(0,"snprintf");

    buffer[necrit] ='\0';
    CHK(write(fd, buffer, necrit));
    CHK(close(fd));
}

char *base (char *chemin)
{
    char *p ;
    p = strrchr (chemin, '/') ;
    return p == NULL ? chemin : p+1 ;
}


/// Reponse aux requetes des clients
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

    // Ecriture dans la base de données le contenu de l'image
    n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, nom) ;
    if (n < 0 || n > CHEMIN_MAX)
        raler(0, "chemin '%s/%s' trop long", rep, nom) ;
    CHK (fd = open (nchemin, O_WRONLY | O_CREAT, 0666)) ;
    CHK (write (fd, &requete[tailleNom + 1 + sizeof tailleContenu], tailleContenu)) ;
    CHK (close (fd)) ;

    // message d'erreur (pas d'erreur)
    reponse[0] = 1; 
    reponse[1] = '\0'; 
    // envoyer la réponse au client
    CHK (write (clientSocket, reponse, 2)) ;
}

void RepListeImages (int clientSocket, char *rep)
{
    struct stat stbuf ;
    DIR *dp ;
    struct dirent *d ;
    
    uint16_t nbNoms = 0;
    int nbOctets = 2;
    int index;
    char *reponse = NULL;
    int n;
    char nchemin [CHEMIN_MAX + 1];

    CHKN(reponse = (char *) realloc (reponse, nbOctets)) ;

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
                    index = nbOctets;
                    nbOctets += strlen(d->d_name) + 1;
                    CHKN (reponse = (char *) realloc (reponse, nbOctets)) ;
                    n = snprintf(reponse + index, strlen(d->d_name) + 1, "%s", d->d_name);
                    if (n < 0)
                        raler (0, "snprintf") ;
                    reponse[nbOctets - 1] = '\n';
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
        CHKN (reponse = (char *) realloc (reponse, nbOctets)) ;
    }
    reponse[nbOctets - 1] = '\0'; 

    //Nombre de noms
    nbNoms = htons(nbNoms);
    memcpy(reponse, &nbNoms, sizeof(nbNoms));
    CHK (write (clientSocket, reponse, nbOctets)) ;

    free (reponse) ;
}

void RepTesterExistenceImage(int clientSocket,char *requete, char *rep)
{
    struct stat stbuf ;
    char nchemin [CHEMIN_MAX + 1];
    char *message = "ce n'est pas un fichier régulier"; 
    int n, existe = 0;
    char reponse[MAXLEN];


    //tailleNom
    char tailleNom = requete[0]; 
    char nom [tailleNom]; // nom de l'image + caractère nul
    memcpy(nom, &requete[1], tailleNom);

    // tester l'existence de l'image
    n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, nom) ;
    if (n < 0 || n > CHEMIN_MAX)
        raler(0, "chemin '%s/%s' trop long", rep, nom) ;
    
    // tester l'existence de l'image
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

    // envoyer la réponse au client
    if (existe)
    {
        // pas d'erreur
        reponse[0] = 1; 
        reponse[1] = '\0'; 
        CHK (write (clientSocket, reponse, 2)) ;
    }
    else
    {
        // longueur du message + caractère nul
        reponse[0] = strlen(message) + 1; 
        memcpy(&reponse[1], message, strlen(message) + 1);
        CHK (write (clientSocket, reponse, strlen(message) + 1)) ;
    }
}

void RepSupImage(int clientSocket,char *requete, char *rep)
{
    char nchemin [CHEMIN_MAX + 1];
    int n;
    char reponse [MAXLEN];

    // tailleNom
    char tailleNom =requete[0]; 
    char nom [(int) tailleNom]; 

    // Recuperer le Nom
    memcpy(nom, &requete[1], tailleNom);
    n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, nom) ;
    if (n < 0 || n > CHEMIN_MAX)
        raler(0, "chemin '%s/%s' trop long", rep, nom) ;
    
    // supression du fichier
    CHK (unlink (nchemin)) ;

    // message d'erreur (pas d'erreur)
    reponse[0] = 1; 
    reponse[1] = '\0'; 

    // envoyer la réponse au client
    CHK (write (clientSocket, reponse, 2)) ;
    printf ("L'image est supprimée de la Base de données\n");
}

void RepRecupImage(int clientSocket,char *requete, char *rep)
{
    char reponse [MAXLEN];
    char nchemin [CHEMIN_MAX + 1];
    int n, fd;
    struct stat stbuf;
    ssize_t nlus;
    uint32_t tailleContenu;


    // tailleNom
    char tailleNom =requete[0]; 
    // Nom
    char nom [(int) tailleNom]; 
    memcpy(nom, &requete[1], tailleNom);
    n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, nom) ;
    if (n < 0 || n > CHEMIN_MAX)
        raler(0, "chemin '%s/%s' trop long", rep, nom) ;

    // tailleContenu
    CHK (lstat (nchemin, &stbuf)) ;
    tailleContenu = htonl (stbuf.st_size) ;
    memcpy (reponse, &tailleContenu, sizeof tailleContenu) ;

    // Contenu 
    CHK (fd = open (nchemin, O_RDONLY)) ;
    CHK (nlus = read (fd, &reponse[sizeof tailleContenu], stbuf.st_size)) ;
    CHK (close (fd)) ;

    // envoyer la réponse au client
    CHK (write (clientSocket, reponse, sizeof tailleContenu + nlus)) ;

    printf ("L'image est envoyée au client\n") ;
}



// Ce que fait le serveur une fois la connexion établie
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
            RepListeImages (clientSocket,rep);
            break;
        case 1: // Reponse à tester l’existence d’une image
            RepTesterExistenceImage(clientSocket,&requete[1],rep);
            break;
        case 2: // Reponse à envoyer une image vers le serveur
            RepSendImageToServer(clientSocket,&requete[1],rep);
            break;
        case 3: // Reponse à récupérer une image depuis le serveur 
            RepRecupImage(clientSocket,&requete[1],rep);
            break;
        case 4: // Reponse à supprimer une image sur le serveur
            RepSupImage(clientSocket,&requete[1],rep);
            break;
        default:
            printf("erreur \n");
        break;
    }
}

// On etablie la connexion avec les clients
void Connexion(const char *serv_adrIPv4, int serv_port, int socketType,char *rep)
{
    int serverSocket;
    struct sockaddr_in serv_addr;

    // Création du socket serveur
    CHK(serverSocket = socket(AF_INET, socketType, 0));

    // Configurer l'adresse du serveur
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = inet_addr(serv_adrIPv4); //INADDR_ANY;
    serv_addr.sin_port = htons( serv_port);  // htons(IMAGE_PORT);

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
    struct sockaddr_in client_adr;
    socklen_t client_adrLen ;
    for (;;) 
    {
        // Accepter les connexions entrantes
        client_adrLen = sizeof(client_adr);
        r = (clientSocket = accept(serverSocket, (struct sockaddr *)&client_adr, &client_adrLen)) ;
        if (r == -1) raler (0,"accept") ;
        printf("Connexion acceptée depuis %s:%d\n", inet_ntoa(client_adr.sin_addr), ntohs(client_adr.sin_port));
        serveur ( clientSocket,rep);
        // Fermer les sockets
        close(clientSocket);
    }
    // Fermeture du socket
    close(serverSocket);

}


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


    // Ecriture les infos dans InfoServeur
    WriteInfoServeur("image", IMAGE_IPV4,image_port);
    WriteInfoServeur("tag", TAG_IPV4,TAG_PORT);
    // WriteInfoServeur("image", IMAGE_IPV4, IMAGE_PORT);

    Connexion(IMAGE_IPV4, IMAGE_PORT, SOCK_STREAM,RepImage);

    return 0;
}