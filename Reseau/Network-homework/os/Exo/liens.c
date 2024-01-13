#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h>
#include <errno.h>
#include <utime.h>
#include <stdarg.h>
#include <stdnoreturn.h>

#define	MAX_CHEMIN	512 
#define	MAX_FICHIER	20

#define	CHK(op)		do { if ((op) == -1) raler (1,#op) ; } while (0)

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



void creer_chemin(char *n, const char *rep, const char *b)
{
    int l;
    l = snprintf(n, MAX_CHEMIN +1, "%s/%s", rep, b);
    if( l == -1 || l > (int) MAX_CHEMIN)
	    raler (0, "chemin '%s/%s' trop long", rep, b) ;

}


typedef struct {
   char *file;
   ino_t ninode;
   int freq ;
} mynewtype;


int compare(const void* a, const void* b) 
{
   int freq_a = ((const mynewtype*) a) ->freq;
   int freq_b = ((const mynewtype*) b)->freq;
   return freq_b - freq_a;
}

// variable global qui compte le nb de fichier
int nb_fichier = 0;

void stocke_fichier(mynewtype Liste_file[], const char *chemin, const ino_t inode)
{
   strcpy(Liste_file[nb_fichier].file, chemin);
   Liste_file[nb_fichier].ninode= inode;
   nb_fichier++;
}


void trier_afficher_dossier(mynewtype Liste_file[], int compare(const void* , const void* ))
{
    if(nb_fichier != 0)
    {
        // on calcule les occurances de chaque fichier
        for (int i = 0; i < nb_fichier; i++) {
            Liste_file[i].freq = 0;
            for (int j = 0; j < nb_fichier; j++) {
                if (Liste_file[i].ninode == Liste_file[j].ninode) {
                    Liste_file[i].freq++;
                }
            }
        }
        // Trier le tableau suivant le nombre d'occurrences freq
        qsort(Liste_file, nb_fichier, sizeof(mynewtype), compare);

            // Affichage des résultats
        int nboccu = Liste_file[0].freq;

        // on considère unique le cas ou l'occurance maximal > 1
        if (nboccu > 1)
        {
            printf("%s", Liste_file[0].file);
            for (int i = 1; i < nb_fichier; i++) 
            {
                if (Liste_file[i].freq > 1)
                {
                    if (Liste_file[i].freq == nboccu) {
                        printf(" ");
                    }
                    else {
                        printf("\n");
                        nboccu = Liste_file[i].freq;
                    }
                    // printf("%s", List_file[i].file);
                    printf("%s", Liste_file[i].file);
                }
            }
            printf("\n");
        }
    }
}


void recherche_liens(const char *rep, mynewtype Liste_file[])
{
    DIR *dp; 
    struct dirent *d;  

    // ouvrir le répertoire rep 
    dp = opendir (rep) ;
    if (dp == NULL )
        raler(1,"opendir");


    // parcourir chaque entrée du répertoire rep
    while ((d = readdir(dp)) != NULL)
    {
        // éliminer . et ..
        if(strcmp ( d->d_name, ".") != 0 && strcmp( d->d_name, "..") !=0)
        {
            // si on arrive ici, c'est que ce n'est ni . et ..
            struct stat stbuf ;
            char* nrep = (char*)malloc((MAX_CHEMIN +1) * sizeof(char));
            if (nrep == NULL)
                raler(1,"malloc");

            //créer le chemin nrep avec rep et d->d_name
            creer_chemin(nrep, rep, d->d_name);

            // on récupère attribut pour savoir si rep ou fichier
            CHK(lstat(nrep, &stbuf));

            switch (stbuf.st_mode & __S_IFMT)
            {
                case __S_IFLNK :
                    // si liens symbolique on fait rien
                    break;
                case __S_IFDIR:
                    // si c'est un répertoire alors appel récursif
                    recherche_liens( nrep, Liste_file);
                    break;
                case __S_IFREG:
                    // si c'est un fichier alors le stocker
                    stocke_fichier( Liste_file, nrep,d->d_ino);
                    break;
                default:
                    break;
            }
            // libère la memoire
            free(nrep);
        }
    }
    CHK(closedir(dp));
}


int main (int argc, const char *argv [])
{
    // vérification de usage
    if(argc != 2) 
        raler(0,"usage : liens repertoire\n");

    //  on alloue de la mémoire pour stocker les fichiers 
    mynewtype *Liste_file = (mynewtype*) malloc(MAX_FICHIER *sizeof(mynewtype));
    for (int i = 0; i < MAX_FICHIER; i++)
       (Liste_file[i]).file = (char*) malloc((MAX_CHEMIN + 1) * sizeof(char));
    

    recherche_liens(argv[1],Liste_file);

    trier_afficher_dossier(Liste_file,compare);


    // on libère la mémoire allouée
    for (int i = 0; i < MAX_FICHIER; i++)
       free((Liste_file[i]).file);
    free(Liste_file);

    exit(0);
}