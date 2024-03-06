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


#define MAXADDRLEN 256
#define MAXPORT 50
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

struct ServeurInfo 
{
    char name[MAXADDRLEN];
    char address[MAXADDRLEN];
    int port;
};

void LireServeurInfo(const char *filename, struct ServeurInfo servers[]) 
{
    int fd;
    ssize_t nlus;
    char buffer[MAXADDRLEN * 2 + MAXPORT*2]; 

    // lecture dans le fichier InfoServeur
    CHK(fd = open(filename, O_RDONLY));
    CHK(nlus = read(fd, buffer, sizeof(buffer) - 1));
    CHK(close(fd));
    buffer[nlus] = '\0'; 

    // récuperation des infos
    if (sscanf(buffer, "%s %s %d %s %s %d",
               servers[0].name, servers[0].address, &servers[0].port,
               servers[1].name, servers[1].address, &servers[1].port) == 6) { // 6 le nombre d'argument reconnus 
    } 
    else 
    {
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


// Connexion au serveur Image
int connectToServer(const char *address, int port, int socketType)
{

    int clientSocket;
    struct sockaddr_in serv_addr;

    // Création d'une socket TCP ou UDP
    CHK(clientSocket = socket(AF_INET, socketType, 0));

    // Configurer l'adresse du serveur
    memset(&serv_addr, 0, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = inet_addr(address);
    serv_addr.sin_port = htons(port);
    
    // Se connecter au serveur TCP
    CHK(connect(clientSocket, (struct sockaddr *)&serv_addr, sizeof(serv_addr)));
    printf("Connecté au serveur %s:%d\n",address, port);

    return clientSocket;
}

// Requete à envoyer au serveur Image 
void ReqSendImageToServer(int clientSocket,unsigned char type, char *nom, char *reponse)
{

    char *filename;
    char requete [MAXLEN];
    uint8_t tailleNom;
    uint32_t tailleContenu;
    int fd;
    struct stat stbuf;
  
   
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

    // Reception de la réponse
    CHK (read (clientSocket, reponse, MAXLEN)) ;
    uint16_t nbNoms;
    memcpy(&nbNoms, reponse, sizeof nbNoms);
    nbNoms = ntohs (nbNoms) ;
    printf("Nombre d'images: %d\n", nbNoms);
    printf("%s\n", &reponse[sizeof nbNoms]);
}

void ReqTesterExistenceImage(int clientSocket,unsigned char type, char *nom, char *reponse)
{
    char requete[MAXLEN];
    char *filename;
    uint8_t tailleNom;


    //type
    requete[0] = type;
    //Basename de nom
    CHKN (filename = basename(nom));
    //tailleNom
    tailleNom = (uint8_t) strlen(filename) + 1; 
    requete[1] =  tailleNom;
    memcpy(&requete[2], filename,  tailleNom);

    //Envoyer la requête au serveur
    CHK (write (clientSocket, requete,  tailleNom + 2)) ;

    // recevoir la réponse
    CHK (read (clientSocket, reponse, MAXLEN)) ;

    if (reponse[0] == 1)
    {
        printf("L'image existe\n");
    }
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


    //type
    requete[0] = type;
    //Basename de nom
    CHKN (filename = basename(nom));
    //tailleNom
    requete[1] = strlen(filename) + 1; 
    memcpy(&requete[2], filename, strlen(filename) + 1);

    //Envoyer la requête au serveur
    CHK (write (clientSocket, requete, 2 + strlen(filename) + 1)) ;

    // puis recevoir la réponse
    CHK (read (clientSocket, reponse, MAXLEN)) ;
    if (reponse[0] == 1)
        printf("L'image a été supprimée de la Base de données\n");
    else
        printf("L'image n'a pas été supprimée de la Base de données\n");
}


void ReqRecupImage(int  clientSocket,unsigned char type, char *nom, char *reponse)
{
    char *filename;
    char requete [MAXLEN];
    uint32_t tailleContenu;
    size_t size;

    //type
    requete[0] = type;
    //tailleNnom
    CHKN (filename = basename(nom));
    requete[1] = strlen(filename) + 1; 
    // Nom
    memcpy(&requete[2], filename, strlen(filename) + 1);

    // Envoyer la requête au serveur
    CHK (write ( clientSocket, requete, 2 + strlen(filename) + 1)) ;

    // puis recevoir la réponse
    CHK (read ( clientSocket, reponse, MAXLEN)) ;

    // en supposant que l'image existe
    // on recupere la tailleContenu
    memcpy(&tailleContenu, reponse, sizeof tailleContenu);
    size = ntohl (tailleContenu) ;


    // Ecrire le contenu de l'image sur la sortie standard
    CHK (write (1, &reponse[sizeof tailleContenu], size)) ;
}


// Requete à envoyer au serveur Tag

void RepListeTagOfImage(int clientSocket,unsigned char type, char *nomImage, char *reponse, struct sockaddr_in *serv_addr)
{

    char *filename;
    char requete [MAXLEN];
    uint8_t tailleNom;
    uint32_t tailleContenu;
    int fd;
    struct stat stbuf;

    //Formation de requete
    //type
    requete[0] = type;
    //tailleNom
    CHKN (filename = basename(nomImage));
    tailleNom = (uint8_t) strlen(filename) + 1; // longueur du nom + caractère nul
    requete[1] = tailleNom ;
    //Nom
    memcpy(&requete[2], filename, strlen(filename) + 1);
    //tailleContenu
    CHK (lstat (nomImage, &stbuf)) ;
    tailleContenu = htonl (stbuf.st_size) ;
    memcpy (&requete[2 + strlen(filename) + 1], &tailleContenu, sizeof tailleContenu) ;
   
   
    // lecture du fichier et écriture dans requete
    CHK (fd = open (nomImage, O_RDONLY)) ;
    CHK ( read (fd, &requete[2 + strlen(filename) + 1 + sizeof tailleContenu], 
            tailleContenu));
    CHK (close (fd)) ;

    
     // Envoyer des données au serveur
    sendto(clientSocket, requete, 2 + strlen(filename) + 1 + sizeof tailleContenu + stbuf.st_size, 0,
           (struct sockaddr *)serv_addr, sizeof(*serv_addr));

    // Reception de la réponse du server
    recvfrom(clientSocket, reponse,
     MAXLEN, 0,(struct sockaddr *) 0, (socklen_t *) 0);

}
   



int main(int argc, char *argv[]) {

    // Lecture fichier "InfoServeur.cfg" 
    struct ServeurInfo servers[2];
    const char *filename = "InfoServeur.cfg";
    LireServeurInfo(filename, servers);

    int serv_port;
    char servIP[MAXADDRLEN];
    // char serv_addr[MAXADDRLEN];
    unsigned char type;


   
    // Nom de l'image
    // char *nom ;
    char *nomImage ;
    // Tag 
    char *nomTag ;
    int nbTag = 10;
    char *ListTag[nbTag] ;
    // Pour recevoir la reponse du serveur
    char reponse[MAXLEN];
  
  
    //coté serveur image
    if (strcmp(argv[1], servers[0].name) == 0)
    {
        // verif nombre d'arguments
        if ((argc != 3) && (argc != 4))
        {
            usage(argv[0]);
        }

        const char *Commandevalable[] = {"list", "test", "add", "get", "del"};
        const char Typevalable[] = {0, 1, 2, 3,4};

        for (int i = 0; i < 5; ++i)
        {
            if (strcmp(argv[2], Commandevalable[i]) == 0)
            {
                strcpy(servIP, servers[0].address); // indice 0 pour "image"
                serv_port = servers[0].port;
                type = Typevalable[i];
                // Recupere le nom du fichier
                if(type  != 0)
                {
                    nomImage = argv[3];
                }
            }
        }
    }
    //coté serveur tag
    else if (strcmp(argv[1], servers[1].name) == 0)
    {

        //list = lister les tags associés à une image
        //image = lister les images associées à un ensemble de tags
        const char *Commandevalable[] = {"list", "image", "add", "del"};
        const char Typevalable[] = {0, 1, 2, 3};

        for (int i = 0; i < 4; ++i)
        {
            if (strcmp(argv[2], Commandevalable[i]) == 0)
            {
                strcpy(servIP, servers[1].address); // indice 0 pour "image"
                serv_port = servers[1].port;
                type = Typevalable[i];
                 // Recupere le nom du fichier type 0
                if(type  == 0)
                {
                    nomImage = argv[3];
                }

                // type 1 
                if(type  == 1)
                {
                    nbTag = argc - 3;
                    for (int j  = 0; j < nbTag; ++i)
                    {
                        ListTag[j] = argv[j+3];
                    }
                }
                //type 2 et 4
                nomImage = argv[3];
                nomTag = argv[4];
            }
        }
    
    }
    // usage : client ... 
    else
    {
        usage(argv[0]);
    }
   

    // connexion dans serveur et tout le reste


    if (strcmp(argv[1], servers[0].name) == 0) // coté image
    {
        // Connexion au serveur concerné Image 
        int clientSocket = connectToServer(servIP, serv_port, SOCK_STREAM);
        printf("Connecté au serveur image en TCP\n");


        // Ici, on la connection est établi


        //Envoyer la requete au serveur Image
        switch (type)
        {
            case 0: // Requete de type : lister les images présentes
                printf("type : %d\n", type);
                ReqListeImage(clientSocket,type,reponse);
                break;
        
            case 1: // Requete de type : tester l’existence d’une image
                printf("type : %d\n", type);
                ReqTesterExistenceImage(clientSocket,type,nomImage,reponse);
                break;
            case 2: // Requete de type : envoyer une image vers le serveur
                printf("type : %d\n", type);
                ReqSendImageToServer(clientSocket,type,nomImage,reponse);
                break;
            case 3: // Requete de type : récupérer une image depuis le serveur 
                // printf("type : %d\n", type);
                ReqRecupImage(clientSocket,type,nomImage,reponse);


                break;
            case 4: // Requete de type : supprimer une image sur le serveur
                printf("type : %d\n", type);
                ReqSupImage(clientSocket,type,nomImage,reponse);
                break;
            default:
                printf("erreur \n");
            break;
        }
        
        // Fermer la socket client
        CHK(close(clientSocket));
    }

    if (strcmp(argv[1], servers[1].name) == 0)  // coté tag
    {
        ///////// Connexion au serveur concerné Tag

        // Création d'une socket UDP
        int clientSocket;

        CHK(clientSocket = socket(AF_INET, SOCK_DGRAM, 0));
        // Configurer l'adresse du serveur
        struct sockaddr_in serv_addr;
        memset(&serv_addr, 0, sizeof(serv_addr));
        serv_addr.sin_family = AF_INET;
        serv_addr.sin_addr.s_addr = inet_addr(servIP);
        serv_addr.sin_port = htons(serv_port);


        printf("Connecté au serveur Tag en UDP\n");

                //Envoyer la requete au serveur Image
        switch (type)
        {
            case 0: // lister les tags associés à une image
                RepListeTagOfImage(clientSocket,type,nomImage,reponse,&serv_addr);
                break;
            default:
                printf("erreur \n");
            break;
        }
        
        (void) nomTag;
        (void) ListTag;
        // Fermer la socket client
        CHK(close(clientSocket));
    }
    

    exit(0);
}



