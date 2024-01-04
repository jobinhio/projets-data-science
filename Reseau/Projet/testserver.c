#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <inttypes.h>

int main() {

char nom[256];  // Taille de 256 pour stocker les 255 octets plus le caractère nul

ssize_t nlus;
CHK(nlus = read(clientSocket, nom, 255));  // Lire 255 octets depuis clientSocket
nom[255] = '\0';  // Terminer la chaîne avec le caractère nul

// Convertir les octets en entier (en supposant une représentation Little-Endian)
unsigned int entier = 0;
for (int i = 0; i < 4; ++i) {
    entier |= (unsigned char)nom[i] << (i * 8);
}

printf("Entier : %u\n", entier);


    return 0;
}
