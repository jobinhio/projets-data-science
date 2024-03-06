#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

void client_udp(int clientSocket, const char *serverIP, int serverPort) {
    struct sockaddr_in serverAddr;

    // Configure the server address
    memset(&serverAddr, 0, sizeof(serverAddr));
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = inet_addr(serverIP);
    serverAddr.sin_port = htons(serverPort);

    // Send data to the server
    const char *dataToSend = "Hello from the client!";
    sendto(clientSocket, dataToSend, strlen(dataToSend), 0,
           (struct sockaddr*)&serverAddr, sizeof(serverAddr));

    // Receive the response from the server
    char buffer[1024];
    ssize_t receivedBytes = recvfrom(clientSocket, buffer, sizeof(buffer), 0, NULL, NULL);

    if (receivedBytes == -1) {
        perror("Error receiving response");
        exit(EXIT_FAILURE);
    }

    buffer[receivedBytes] = '\0';
    printf("Received from server: %s\n", buffer);
}

int main() {
    int clientSocket;
    
    // Create a UDP socket
    clientSocket = socket(AF_INET, SOCK_DGRAM, 0);
    if (clientSocket == -1) {
        perror("Error creating socket");
        exit(EXIT_FAILURE);
    }

    // Replace "127.0.0.1" with the server's IP address
    // and 5000 with the port the server is listening on
    client_udp(clientSocket, "127.0.0.1", 5000);

    // Close the socket
    close(clientSocket);

    return 0;
}
