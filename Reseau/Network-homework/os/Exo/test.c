#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <errno.h>
#include <stdarg.h>
#include <stdnoreturn.h>
#include <stdint.h>
#include <signal.h>

#define FILENAME "entiers.txt"
#define MAX_ENTIERS 10

int main() {
    pid_t pid;
    int fd, i, entier;

    // Ouverture du fichier en écriture
    if ((fd = open(FILENAME, O_WRONLY | O_CREAT | O_TRUNC, 0644)) == -1) {
        perror("Erreur lors de l'ouverture du fichier");
        exit(EXIT_FAILURE);
    }

    // Écriture de plusieurs entiers dans le fichier
    for (i = 0; i < MAX_ENTIERS; i++) {
        entier = i + 1;
        if (write(fd, &entier, sizeof(int)) == -1) {
            perror("Erreur lors de l'écriture dans le fichier");
            exit(EXIT_FAILURE);
        }
    }

    // Fermeture du fichier
    close(fd);

    // Création de plusieurs processus fils
    for (i = 0; i < MAX_ENTIERS; i++) {
        pid = fork();
        if (pid == -1) {
            perror("Erreur lors de la création du processus fils");
            exit(EXIT_FAILURE);
        } else if (pid == 0) { // Code exécuté par le processus fils
            if ((fd = open(FILENAME, O_RDONLY)) == -1) {
                perror("Erreur lors de l'ouverture du fichier");
                exit(EXIT_FAILURE);
            }

            // Lecture de l'entier correspondant au processus fils
            if (lseek(fd, i * sizeof(int), SEEK_SET) == -1) {
                perror("Erreur lors du positionnement dans le fichier");
                exit(EXIT_FAILURE);
            }

            if (read(fd, &entier, sizeof(int)) == -1) {
                perror("Erreur lors de la lecture dans le fichier");
                exit(EXIT_FAILURE);
            }

            printf("Processus fils %d : entier lu = %d\n", getpid(), entier);

            // Fermeture du fichier
            close(fd);

            // Fin du processus fils
            exit(EXIT_SUCCESS);
        }
    }

    // Attente de la fin de tous les processus fils
    for (i = 0; i < MAX_ENTIERS; i++) {
        wait(NULL);
    }

    return 0;
}