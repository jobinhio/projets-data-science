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




void traiter_requete(int in, char *requete)
{
    // Extraire le type de requête du premier octet
    char type = requete[0];

    // Pointeur pour parcourir la requête
    char *ptr = requete + 1;

    switch (type)
    {
        case 0: // Requête de lister les images présentes
        {
            // Traitement de la requête de listage
            // ...

            // Exemple de réponse : une liste de noms
            char liste_noms[] = {2, 'i', 'm', 'g', '1', 'i', 'm', 'g', '2'};
            write(in, liste_noms, sizeof(liste_noms));
            break;
        }
        case 1: // Requête de tester l'existence d'une image
        {
            // Extraire le nom de la requête
            int len = (unsigned char)*ptr;
            ptr++;
            char nom[len + 1];
            strncpy(nom, ptr, len);
            nom[len] = '\0';

            // Traitement de la requête de test d'existence
            // ...

            // Exemple de réponse : une erreur
            char erreur[] = {7, 'E', 'r', 'r', 'e', 'u', 'r'};
            write(in, erreur, sizeof(erreur));
            break;
        }
        case 2: // Requête d'envoyer une image vers le serveur
        {
            // Extraire le nom et le contenu de la requête
            int len_nom = (unsigned char)*ptr;
            ptr++;
            char nom[len_nom + 1];
            strncpy(nom, ptr, len_nom);
            nom[len_nom] = '\0';
            ptr += len_nom;

            int len_contenu = *((int *)ptr);
            ptr += sizeof(int);
            char contenu[len_contenu];
            strncpy(contenu, ptr, len_contenu);

            // Traitement de la requête d'envoi d'image
            // ...

            // Exemple de réponse : une erreur
            char erreur[] = {5, 'O', 'K'};
            write(in, erreur, sizeof(erreur));
            break;
        }
        case 3: // Requête de récupérer une image depuis le serveur
        {
            // Extraire le nom de la requête
            int len = (unsigned char)*ptr;
            ptr++;
            char nom[len + 1];
            strncpy(nom, ptr, len);
            nom[len] = '\0';

            // Traitement de la requête de récupération d'image
            // ...

            // Exemple de réponse : le nom et le contenu de l'image
            int len_reponse = 9 + strlen(nom) + 1 + sizeof(int) + 7;
            char reponse[len_reponse];
            reponse[0] = (unsigned char)(strlen(nom) + 1);
            strncpy(reponse + 1, nom, strlen(nom) + 1);
            *((int *)(reponse + 1 + strlen(nom) + 1)) = 7;
            strncpy(reponse + 1 + strlen(nom) + 1 + sizeof(int), "Contenu", 7);
            write(in, reponse, len_reponse);
            break;
        }
        case 4: // Requête de supprimer une image sur le serveur
        {
            // Extraire le nom de la requête
            int len = (unsigned char)*ptr;
            ptr++;
            char nom[len + 1];
            strncpy(nom, ptr, len);
            nom[len] = '\0';

            // Traitement de la requête de suppression d'image
            // ...

            // Exemple de réponse : une erreur
            char erreur[] = {6, 'D', 'e', 'l', 'e', 't', 'e'};
            write(in, erreur, sizeof(erreur));
            break;
        }
        default:
            // Type de requête non pris en charge
            break;
    }
}


void serveur (int in)
{
    int r ;
    char buf [MAXLEN] ;
    int n ;

    n = 0 ;
    while ((r = read (in, buf, MAXLEN)) > 0)
	n += r ;
    printf ("%d\n", n) ;
}


void Connexion(const char *serv_adrIPv4, int serv_port, int socketType)
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

    // Fermer les sockets
    close(clientSocket);
    close(serverSocket);
   

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

    

}

int main()
{
    // Ecriture dans InfoServeur
    WriteInfoServeur("image", IMAGE_IPV4, IMAGE_PORT);
    WriteInfoServeur("tag", TAG_IPV4,TAG_PORT);

    // Exemple d'utilisation pour un serveur TCP
    Connexion(IMAGE_IPV4, IMAGE_PORT, SOCK_STREAM);


    return 0;
}