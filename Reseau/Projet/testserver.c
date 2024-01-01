#include <stdio.h>

int main() {
    // Chaîne de caractères
    const char *chaine = "0031";

    // Variable pour stocker la valeur convertie
    unsigned int val;

    // Utiliser sscanf pour convertir la chaîne en unsigned int
    if (sscanf(chaine, "%u", &val) == 1) {
        // Afficher la valeur convertie
        printf("La valeur convertie est : %u\n", val);
    } else {
        // Gérer les erreurs de conversion
        printf("Erreur de conversion\n");
    }

    return 0;
}
