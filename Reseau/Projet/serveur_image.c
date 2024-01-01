#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <utime.h>
#include <stdarg.h>
#include <stdnoreturn.h>
#include <stdint.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define InfoServeur "InfoServeur.cfg"
#define IMAGE_IPV4 "127.0.0.1"
#define IMAGE_PORT 8080

#define TAG_IPV4 "127.0.0.1"
#define TAG_PORT 9090


#define	CHEMIN_MAX	512
#define MAXLEN 256
#define MAX_ADDR_LEN 256

#define	CHK(op)		do { if ((op) == -1) raler (1, #op) ; } while (0)

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

void serveur ( int clientSocket,char *rep)
{

    // reception des requetes

    // pour le type de requete recu
    ssize_t nlus ;
    unsigned char type ;
    CHK(nlus = read(clientSocket, &type, 1));
    printf("type : %d\n", type);

    
    char nom[MAXLEN];  
    unsigned char chaine[4];
    char Contenu[MAXLEN];  
    char filename[CHEMIN_MAX + 1] ;
    char *b ;




    switch (type)
    {
        case 0: // lister les images présentes
            printf("type : %d\n", type);
            break;
    
        case 1: // tester l’existence d’une image
            printf("type : %d\n", type);
            break;
        case 2: // envoyer une image vers le serveur

            // Parametres: nom et contenu

            // nom de l'image 
            unsigned char tailleNom ;
            CHK(nlus = read(clientSocket, &tailleNom, 1));
            CHK(nlus = read(clientSocket, nom, tailleNom ));
            nom[tailleNom] = '\0';  // Terminer la chaîne avec le caractère nul
            printf("tailleNom: %d\n", tailleNom);
            printf("nom : %s\n", nom);



            // Taillecontenu 
            unsigned int tailleContenu;
            CHK(nlus = read(clientSocket,chaine, 4));
            chaine[4]= '\0';
            if (sscanf(chaine, "%u", &tailleContenu) == 1) {
                // Afficher la valeur convertie
                printf("tailleContenu: %u\n", tailleContenu);
            } else {
                // Gérer les erreurs de conversion
                printf("Erreur de conversion\n");
            }

            // creer fichier de nom : nom
            int n;
            n = snprintf (filename, filename, "%s/%s", rep, nom) ;
            if (n < 0 || n > CHEMIN_MAX)
                raler (0, "chemin '%s/%s' trop long", rep, nom) ;

            printf("filename : %s\n", filename);
            
            int fd ;
            CHK (fd = open (filename, O_WRONLY | O_CREAT | O_TRUNC, 0666)) ;

            while ((nlus = read (clientSocket,Contenu, tailleContenu)) > 0)
            CHK (write (fd, Contenu, nlus)) ;
            CHK (nlus) ;
            CHK (close (fd)) ;




            // CHK(nlus = read(clientSocket,Contenu, tailleContenu));
            // Contenu[tailleContenu] = '\0';  // Terminer la chaîne avec le caractère nul
            // printf("Contenu : %s\n", Contenu);

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



    // Envoyer des données au client
    const char *response = "Bonjour, client!\n";
    CHK(write(clientSocket, response, strlen(response))) ;

    
}


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