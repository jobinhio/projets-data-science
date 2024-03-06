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
    int necrit = snprintf(buffer, sizeof(buffer), "%s %s %d\n", serverName, serv_adrIPv4, serv_port);
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



/// Reponse
// Fonction pour vérifier la présence d'une chaîne dans fichier
int lireEtVerifier(const char *nomFichier, const char *chaineAVerifier) 
{
    // Ouvrir le fichier en lecture seule
    int fd;
    CHK((fd = open(nomFichier, O_RDONLY)));

    // Buffer pour stocker les données lues du fichier
    char buffer[1024];
    
    // Lire le fichier
    ssize_t nlus;
    while ((nlus = read(fd, buffer, sizeof(buffer))) > 0) 
    {
        // Rechercher la chaîne dans le buffer
        char *position = strstr(buffer, chaineAVerifier);

        // Si la chaîne est trouvée, fermer le fichier et retourner le succès
        if (position != NULL) 
        {
            close(fd);
            return 1; // La chaîne est présente
        }
    }

    // Fermer le fichier, ici la chaine n'est pas trouvée
    close(fd);
    return 0;
}

void RepListeTagOfImage(int clientSocket,char *requete, char *rep,
    struct sockaddr_in clientAddr,socklen_t clientAddrLen)
{

    //recuperation de tailleNom
    char tailleNom = requete[0]; 
    char nom [(int) tailleNom]; 

    //Nom fichier
    memcpy(nom, &requete[1], tailleNom);


    // Parcourir le repertoire RepTag
    DIR *dp ;
    struct dirent *d ;
    uint16_t NbTags =0;
    int nbOctets = 2;
    int index;


    char reponse [MAXLEN];
    char nchemin [CHEMIN_MAX + 1];
    int n;


    CHKN (dp = opendir (rep)) ;
    while ((d = readdir (dp)) != NULL)
    {
        if (strcmp (d->d_name, ".") != 0 && strcmp (d->d_name, "..") != 0)
        {
            n = snprintf (nchemin, sizeof nchemin, "%s/%s", rep, d->d_name) ;
            if (n < 0 || n > CHEMIN_MAX)
                raler(0, "chemin '%s/%s' trop long", rep, d->d_name) ;


            // Verifier que ce nom est dans le ficher Tag associé  
            if (lireEtVerifier(nchemin, nom)) 
            {

                // Ecire dans reponse 
                index = nbOctets;
                nbOctets += strlen(nchemin) + 1;
                n = snprintf(reponse + index, strlen(nchemin) + 1, "%s", nchemin);
                if (n < 0)
                    raler (0, "snprintf") ;
                reponse[nbOctets - 1] = '\n';
                NbTags++;
            }
        }
    }
    CHK (closedir (dp)) ;

    if (nbOctets == 2) // pas d'images dans le répertoire
    {
        nbOctets += 1;
    }
    reponse[nbOctets - 1] =  '\0'; 

    // Les 2 octets indiquant le nombre de Tag
    NbTags = htons(NbTags);
    memcpy(reponse, &NbTags, sizeof(NbTags));

    
    // Envoyer la reponse au client
    sendto(clientSocket, reponse, nbOctets, 0,
            (struct sockaddr*)&clientAddr, clientAddrLen);
}


void serveur ( int clientSocket,char *rep,struct sockaddr_in clientAddr,socklen_t clientAddrLen )
{
    // lecture entiere du la requete du client
    char requete [MAXLEN] ;

    // Reception des donnes du client
    ssize_t nrecu = recvfrom(clientSocket,&requete, MAXLEN, 0,
                                    (struct sockaddr*)&clientAddr, &clientAddrLen);
    CHK(nrecu);

    char type = requete[0];
    switch (type)
    {
        case 0: // Reponse à lister les tags associés à une image
           RepListeTagOfImage(clientSocket,&requete[0],rep,clientAddr,clientAddrLen);
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

    // Création du socket serveur
    CHK(serverSocket = socket(AF_INET, socketType, 0));

    // Configurer l'adresse du serveur
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = inet_addr(serv_adrIPv4);
    serv_addr.sin_port = htons(serv_port);

    // Lier la socket à l'adresse et au port
    int r;
    r = bind(serverSocket, (struct sockaddr *)&serv_addr, sizeof(serv_addr));
    if (r == -1) raler(0, "bind");

    printf("Le serveur écoute sur le port %d...\n", serv_port);


    struct sockaddr_in clientAddr;
    socklen_t clientAddrLen = sizeof(clientAddr);

    serveur(serverSocket, rep, clientAddr,clientAddrLen);
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
    char *RepTag = argv[2];

    // Ecriture dans InfoServeur pour communiquer au client
    WriteInfoServeur("tag", TAG_IPV4, tag_port);    
    
    Connexion(TAG_IPV4, tag_port, SOCK_DGRAM,RepTag);

    return 0;
}