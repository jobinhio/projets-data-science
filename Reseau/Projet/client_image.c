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


#define MAX_ADDR_LEN 256
#define MAX_PORT 50

#define	MAXLEN	1024


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

struct ServeurInfo {
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
    fprintf (stderr, "usage: %s tag add image tag\n", argv0) ;
    fprintf (stderr, "usage: %s tag del image tag\n", argv0) ;
    fprintf (stderr, "usage: %s tag image tag ... tag\n", argv0) ;
    exit (1) ;
}





void connectToServer(const char *address, int port, int socketType)
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
    if (connect(clientSocket, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) == -1) {
        perror("Erreur lors de la connexion au serveur");
        exit(EXIT_FAILURE);
    }

    printf("Connecté au serveur %s:%d\n",address, port);

    // Ici, vous pouvez interagir avec le serveur en utilisant clientSocket

    // Fermer la socket client
    close(clientSocket);

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


    // usage : client ... et recupération servers 
    if (argc < 4)
    {
        usage(argv[0]);
    }

    if (strcmp(argv[1], servers[0].name) == 0 && argc == 4)
    {
        const char *validCommands[] = {"add", "del", "tag", "get"};

        for (size_t i = 0; i < sizeof(validCommands) / sizeof(validCommands[0]); ++i)
        {
            if (strcmp(argv[2], validCommands[i]) == 0)
            {
                strcpy(serv_addr, servers[0].address); // indice 0 pour "image"
                serv_port = servers[0].port;
            }
        }
    }

    else if (strcmp(argv[1], servers[1].name) == 0)
    {
        const char *validCommands[] = {"add", "del", "image"};

        for (size_t i = 0; i < sizeof(validCommands) / sizeof(validCommands[0]); ++i)
        {
            if (strcmp(argv[2], validCommands[i]) == 0)
            {
                strcpy(serv_addr, servers[1].address); // indice 0 pour "image"
                serv_port = servers[1].port;
            }
        }
    }
    else
    {
        usage(argv[0]);
    }
   


    // Connexion au serveur concerné
    connectToServer(serv_addr, serv_port, SOCK_STREAM);
    printf("Connecté au serveur image en TCP\n");



    exit(0);
}



