#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define PORT 8080

int main() {
    int serverSocket;
    struct sockaddr_in serverAddr;

    // Créer une socket
    if ((serverSocket = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
        perror("Erreur lors de la création de la socket");
        exit(EXIT_FAILURE);
    }

    // Configurer l'adresse du serveur
    memset(&serverAddr, 0, sizeof(serverAddr));
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY;
    serverAddr.sin_port = htons(PORT);

    // Lier la socket à l'adresse et au port
    if (bind(serverSocket, (struct sockaddr *)&serverAddr, sizeof(serverAddr)) == -1) {
        perror("Erreur lors de la liaison de la socket");
        exit(EXIT_FAILURE);
    }

    // Mettre la socket en mode écoute
    if (listen(serverSocket, 5) == -1) {
        perror("Erreur lors de la mise en écoute de la socket");
        exit(EXIT_FAILURE);
    }

    printf("Le serveur écoute sur le port %d...\n", PORT);

    // Accepter les connexions entrantes
    int clientSocket;
    struct sockaddr_in clientAddr;
    socklen_t clientAddrLen = sizeof(clientAddr);

    if ((clientSocket = accept(serverSocket, (struct sockaddr *)&clientAddr, &clientAddrLen)) == -1) {
        perror("Erreur lors de l'acceptation de la connexion");
        exit(EXIT_FAILURE);
    }

    printf("Connexion acceptée depuis %s:%d\n", inet_ntoa(clientAddr.sin_addr), ntohs(clientAddr.sin_port));

    // Ici, vous pouvez interagir avec le client en utilisant clientSocket

    // Fermer les sockets
    close(clientSocket);
    close(serverSocket);

    return 0;
}
