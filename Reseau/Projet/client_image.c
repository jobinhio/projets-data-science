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

#define MAX_ADDR_LEN 256
#define MAX_PORT 50

#define	MAX_REQ_LEN	1048576
// #define MAXLEN	(uint32_t)2818963800000
#define MAXLEN	1048576

#define	MAX_NOM_LEN 255 //  2^8 -1
#define	MAX_ERREUR_LEN 255 //  2^8 -1
#define	MAX_CONTENU_LEN  65535 //  2^16 -1







#define	NOM "%c%s" // 1 octet + nom
#define	ERREUR "%c%s" // 1 octet + message
#define	CONTENU "%04u%s" // 4 octet + contenu
#define	LISTNOM "%02u%s" // 2 octet + liste de noms

#define	CHKN(op)	do { if ((op) == NULL) raler (1, #op) ; } while (0)


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

struct ServeurInfo 
{
    char name[MAX_ADDR_LEN];
    char address[MAX_ADDR_LEN];
    int port;
};

void LireServeurInfo(const char *filename, struct ServeurInfo servers[]) {
    int fd;
    ssize_t nlus;
    char buffer[MAX_ADDR_LEN * 2 + MAX_PORT*2]; 

    // lecture dans le fichier InfoServeur
    CHK(fd = open(filename, O_RDONLY));
    CHK(nlus = read(fd, buffer, sizeof(buffer) - 1));
    CHK(close(fd));

    buffer[nlus] = '\0'; // placer l'octet nul à la fin

    // récuperation des infos
    if (sscanf(buffer, "%s %s %d %s %s %d",
               servers[0].name, servers[0].address, &servers[0].port,
               servers[1].name, servers[1].address, &servers[1].port) == 6) { // 6 le nombre d'argument reconnus 
    } else {
        raler (0, "Format incorrect dans le fichier") ;
    }
}

void usage (char *argv0)
{
    fprintf (stderr, "usage: %s image add image\n", argv0) ;
    fprintf (stderr, "usage: %s image del image\n", argv0) ;
    fprintf (stderr, "usage: %s image tag image\n", argv0) ;
    fprintf (stderr, "usage: %s image get image\n", argv0) ;
    fprintf (stderr, "usage: %s image list\n", argv0) ;
    fprintf (stderr, "usage: %s tag add image tag\n", argv0) ;
    fprintf (stderr, "usage: %s tag del image tag\n", argv0) ;
    fprintf (stderr, "usage: %s tag image tag ... tag\n", argv0) ;
    exit (1) ;
}

int connectToServer(const char *address, int port, int socketType)
{

    int clientSocket;
    struct sockaddr_in serv_addr;

    // Création d'une socket TCP
    CHK(clientSocket = socket(AF_INET, socketType, 0));

    // Configurer l'adresse du serveur
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = inet_addr(address);
    serv_addr.sin_port = htons(port);

    // Se connecter au serveur
    CHK(connect(clientSocket, (struct sockaddr *)&serv_addr, sizeof(serv_addr)));
    printf("Connecté au serveur %s:%d\n",address, port);

    return clientSocket;
}


/// Requete
void ReqSendImageToServer(int clientSocket,unsigned char type, char *nom, char *reponse)
{

    char *filename;
    char requete [MAXLEN];
    uint8_t tailleNom;
    uint32_t tailleContenu;
    int fd;
    struct stat stbuf;
    ssize_t nlus;
   
    //Formation de requete
    //type
    requete[0] = type;
    //tailleNom
    CHKN (filename = basename(nom));
    tailleNom = (uint8_t) strlen(filename) + 1; // longueur du nom + caractère nul
    requete[1] = tailleNom ;
    //Nom
    memcpy(&requete[2], filename, strlen(filename) + 1);
    //tailleContenu
    CHK (lstat (nom, &stbuf)) ;
    tailleContenu = htonl (stbuf.st_size) ;
    memcpy (&requete[2 + strlen(filename) + 1], &tailleContenu, sizeof tailleContenu) ;
    // lecture du fichier et écriture dans requete
    CHK (fd = open (nom, O_RDONLY)) ;
    CHK ( read (fd, &requete[2 + strlen(filename) + 1 + sizeof tailleContenu], 
            tailleContenu));
    CHK (close (fd)) ;

    // Envoyer des données au serveur
    CHK (write (clientSocket, requete, 2 + strlen(filename) + 1 + sizeof tailleContenu + 
            stbuf.st_size)) ;


    // Reception de la réponse du server
    CHK (read (clientSocket, reponse, MAXLEN)) ;

    if (reponse[0] == 1)
        printf("L'image a été ajoutée\n");
    else
        printf("L'image n'a pas été ajoutée\n");
    
}




void ReqListeImage(int clientSocket,unsigned char type, char *reponse)
{
    
    //Envoyer la requête au serveur
    CHK (write (clientSocket, &type, 1)) ;

    // Recevoir de la réponse
    CHK (read (clientSocket, reponse, MAXLEN)) ;
    uint16_t nbImages;
    // on extrait le nombre d'images de reponse
    memcpy(&nbImages, reponse, sizeof nbImages);
    nbImages = ntohs (nbImages) ;
    printf("Nombre d'images: %d\n", nbImages);
    printf("%s\n", &reponse[sizeof nbImages]);
}

void ReqTesterExistenceImage(int clientSocket,unsigned char type, char *nom, char *reponse)
{
    int r;
    char requete[MAXLEN];
    char *filename;
    uint8_t tailleNom;


    //type
    requete[0] = type;
    //Basename de nom
    CHKN (filename = basename(nom));
    //tailleNom
    tailleNom = (uint8_t) strlen(filename) + 1; // longueur du nom + caractère nul
    requete[1] =  tailleNom;
    // memcpy(&requete[2], nom,  tailleNom);
    memcpy(&requete[2], filename,  tailleNom);
    // doit d'abord envoyer une requête au serveur
    CHK (write (clientSocket, requete,  tailleNom + 2)) ;

    // puis recevoir la réponse
    CHK (r = read (clientSocket, reponse, MAXLEN)) ;

    if (reponse[0] == 1) // octet nul
        printf("L'image existe\n");
    else
    {
        printf("L'image n'existe pas\n");
        printf("%s\n", &reponse[1]);
    }
}

void ReqSupImage(int clientSocket,unsigned char type, char *nom, char *reponse)
{
    char *filename;
    char requete [MAXLEN];


    // doit d'abord envoyer une requête au serveur
    requete[0] = type;
    CHKN (filename = basename(nom));
    requete[1] = strlen(filename) + 1; // longueur du nom + caractère nul
    memcpy(&requete[2], filename, strlen(filename) + 1);
    CHK (write (clientSocket, requete, 2 + strlen(filename) + 1)) ;

    // puis recevoir la réponse
    CHK (read (clientSocket, reponse, MAXLEN)) ;
    if (reponse[0] == 1)
        printf("L'image a été supprimée\n");
    else
        printf("L'image n'a pas été supprimée\n");
}




void ReqRecupImage(int s,unsigned char type, char *nom, char *reponse)
{
    char *filename;
    char requete [MAXLEN];
    
    // doit d'abord envoyer une requête au serveur
    requete[0] = type;
    CHKN (filename = basename(nom));
    requete[1] = strlen(filename) + 1; // longueur du nom + caractère nul
    memcpy(&requete[2], filename, strlen(filename) + 1);
    CHK (write (s, requete, 2 + strlen(filename) + 1)) ;





    // puis recevoir la réponse
    CHK (read (s, reponse, MAXLEN)) ;

    uint32_t taille;
    off_t taillestbuf;

        // en supposant que l'image existe
    // on extrait la taille de l'image de reponse
    memcpy(&taille, reponse, sizeof taille);
    taillestbuf = ntohl (taille) ;

    printf ("taillestbuf = %lu\n", taillestbuf) ;

    // on écrit le contenu de l'image sur la sortie standard
    // CHK (necrit = write (1, &reponse[sizeof taille], taillestbuf)) ;



    size_t necrit;
    int fd ;
    CHK (fd = open ("/home/congo/Reseau/Projet/image.jpg", O_WRONLY)) ;
    CHK (necrit = write (fd, &reponse[sizeof taille], taillestbuf)) ;
    printf ("necrit = %lu\n", necrit) ;


}


int main(int argc, char *argv[]) {

    // Lecture fichier "InfoServeur.cfg" 
    struct ServeurInfo servers[2];
    const char *filename = "InfoServeur.cfg";
    LireServeurInfo(filename, servers);

    /*
    printf("Informations du serveur lues à partir du fichier :\n");
    for (int i = 0; i < 2; i++) {
        printf("Serveur %d: Nom = %s, Adresse = %s, Port = %d\n", i + 1, servers[i].name, servers[i].address, servers[i].port);
    }
    */

    int serv_port;
    char serv_addr[MAX_ADDR_LEN];
    unsigned char type;


   
    // Nom de l'image
    char *nom ;

      // Pour recevoir la reponse du serveur
    char reponse[MAX_REQ_LEN];
  
  
    if ((argc != 3) && (argc != 4))
    {
        usage(argv[0]);
    }

    //coté serveur image
    if (strcmp(argv[1], servers[0].name) == 0)
    {
        const char *Commandevalable[] = {"list", "test", "add", "get", "del"};
        const char Typevalable[] = {0, 1, 2, 3,4};

        for (size_t i = 0; i < sizeof(Commandevalable) / sizeof(Commandevalable[0]); ++i)
        {
            if (strcmp(argv[2], Commandevalable[i]) == 0)
            {
                strcpy(serv_addr, servers[0].address); // indice 0 pour "image"
                serv_port = servers[0].port;
                type = Typevalable[i];
                // Recupere le nom du fichier
                if(type  != 0)
                {
                    nom = argv[3];
                }
            }
        }
    }

    //coté serveur tag
    else if (strcmp(argv[1], servers[1].name) == 0)
    {
        const char *Commandevalable[] = {"add", "del", "image"};

        for (size_t i = 0; i < sizeof(Commandevalable) / sizeof(Commandevalable[0]); ++i)
        {
            if (strcmp(argv[2], Commandevalable[i]) == 0)
            {
                strcpy(serv_addr, servers[1].address); // indice 0 pour "image"
                serv_port = servers[1].port;
            }
        }
    }
    // usage : client ... 
    else
    {
        usage(argv[0]);
    }
   


    // Connexion au serveur concerné
    int clientSocket = connectToServer(serv_addr, serv_port, SOCK_STREAM);
    printf("Connecté au serveur image en TCP\n");


    // Ici, on la connection est établi


    //Envoyer requete au serveur Image
    switch (type)
    {
        case 0: // Requete de type : lister les images présentes
            printf("type : %d\n", type);
            ReqListeImage(clientSocket,type,reponse);
            break;
    
        case 1: // Requete de type : tester l’existence d’une image
            printf("type : %d\n", type);
            ReqTesterExistenceImage(clientSocket,type,nom,reponse);
            break;
        case 2: // Requete de type : envoyer une image vers le serveur
            printf("type : %d\n", type);
            ReqSendImageToServer(clientSocket,type,nom,reponse);
            break;
        case 3: // Requete de type : récupérer une image depuis le serveur 
            // printf("type : %d\n", type);
            ReqRecupImage(clientSocket,type,nom,reponse);


            break;
        case 4: // Requete de type : supprimer une image sur le serveur
            printf("type : %d\n", type);
            ReqSupImage(clientSocket,type,nom,reponse);
            break;
        default:
            printf("erreur \n");
        break;
    }
    

    // Fermer la socket client
    CHK(close(clientSocket));

 

    exit(0);
}



