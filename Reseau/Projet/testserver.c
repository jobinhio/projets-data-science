#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define MAXLEN 1024

void server_udp(int serverSocket) {
    struct sockaddr_in clientAddr;
    socklen_t clientAddrLen = sizeof(clientAddr);
    char buffer[MAXLEN];

    while (1) {
        // Receive data from client
        ssize_t receivedBytes = recvfrom(serverSocket, buffer, MAXLEN, 0,
                                        (struct sockaddr*)&clientAddr, &clientAddrLen);

        if (receivedBytes == -1) {
            perror("Error receiving data");
            break;
        }

        buffer[receivedBytes] = '\0';
        printf("Received from client: %s\n", buffer);

        // Process received data or perform some action

        // Send a response to the client
        const char *response = "Hello from the server!";
        sendto(serverSocket, response, strlen(response), 0,
               (struct sockaddr*)&clientAddr, clientAddrLen);
    }
}

int main() {
    int serverSocket;
    struct sockaddr_in serverAddr;

    // Create a UDP socket
    serverSocket = socket(AF_INET, SOCK_DGRAM, 0);
    if (serverSocket == -1) {
        perror("Error creating socket");
        exit(EXIT_FAILURE);
    }

    // Configure the server address
    memset(&serverAddr, 0, sizeof(serverAddr));
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY;
    serverAddr.sin_port = htons(5000); // Change this to the desired port

    // Bind the socket to the server address
    if (bind(serverSocket, (struct sockaddr*)&serverAddr, sizeof(serverAddr)) == -1) {
        perror("Error binding socket");
        close(serverSocket);
        exit(EXIT_FAILURE);
    }

    printf("Server is listening on port 5000...\n");

    // Call the server function to handle incoming data
    server_udp(serverSocket);

    // Close the socket
    close(serverSocket);

    return 0;
}

