#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define PORT 8080
#define SERVER_ADDRESS "127.0.0.1"  // Adresse IP du serveur

int main() {
    int clientSocket;
    struct sockaddr_in serverAddr;

    // Créer une socket
    if ((clientSocket = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
        perror("Erreur lors de la création de la socket client");
        exit(EXIT_FAILURE);
    }

    // Configurer l'adresse du serveur
    memset(&serverAddr, 0, sizeof(serverAddr));
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = inet_addr(SERVER_ADDRESS);
    serverAddr.sin_port = htons(PORT);

    // Se connecter au serveur
    if (connect(clientSocket, (struct sockaddr *)&serverAddr, sizeof(serverAddr)) == -1) {
        perror("Erreur lors de la connexion au serveur");
        exit(EXIT_FAILURE);
    }

    printf("Connecté au serveur %s:%d\n", SERVER_ADDRESS, PORT);

    // Ici, vous pouvez interagir avec le serveur en utilisant clientSocket

    // Fermer la socket client
    close(clientSocket);

    return 0;
}
