#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define CHK(expr) if ((expr) == -1) { perror(#expr); exit(EXIT_FAILURE); }

int connectToServer(const char *address, int port, int socketType) {
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
    printf("Connecté au serveur %s:%d\n", address, port);

    return clientSocket;
}

int main() {
    const char *serverAddress = "127.0.0.1";
    const int serverPort = 8080;
    const int socketType = SOCK_STREAM;

    // Se connecter au serveur
    int clientSocket = connectToServer(serverAddress, serverPort, socketType);

    // Envoyer des données au serveur
    const char *message = "Bonjour, serveur!";
    if (send(clientSocket, message, strlen(message), 0) == -1) {
        perror("Erreur lors de l'envoi des données au serveur");
    }

    // Recevoir des données du serveur
    char buffer[1024];
    ssize_t bytesRead = recv(clientSocket, buffer, sizeof(buffer), 0);
    if (bytesRead == -1) {
        perror("Erreur lors de la réception des données du serveur");
    } else {
        buffer[bytesRead] = '\0';
        printf("Données reçues du serveur : %s\n", buffer);
    }

    // Fermer la socket
    close(clientSocket);

    return 0;
}
