#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <errno.h>
#include <utime.h>
#include <libgen.h>



#define	MAX_CHEMIN	512
#define	CHK(op)		do { if ((op) == -1) raler (#op) ; } while (0)


void raler (const char *msg)
{
	perror (msg) ;
    exit (1) ;
}


void creer_chemin(char *nfile, const char *rep, const char *bnamefilei)
{
    int l;

    l = snprintf(nfile, MAX_CHEMIN, "%s/%s", rep, bnamefilei);
    if( l == -1 || l >= (int) MAX_CHEMIN)
    {
        fprintf(stderr, "chemin trop long\n");
        exit(1);
    }
}


void copie_fichier( const char *filei, const char *nfilei, const struct stat *stbuf, size_t taille)
{
    int fdi, nfdi ;
    char buffer [taille];
    ssize_t nlus;
    struct utimbuf ut;

    // ouvrir filei et creer nfilei 
    CHK (fdi = open(filei,O_RDONLY)) ;
    CHK (nfdi = open(nfilei,O_WRONLY |O_CREAT | O_TRUNC, 0666)) ;

    // recopier par bloc taille
    while(( nlus = read(fdi, buffer, sizeof buffer)) > 0) 
        CHK(write(nfdi, buffer, nlus)); 

    // nlus vaut 0( fin de fichier) ou -1(erreur) 
    CHK(nlus);

    // pour conserver les permissions 
    CHK(fchmod( nfdi, stbuf->st_mode & 0777));

    // fermer les fichiers
    CHK( close (fdi )) ;
    CHK( close (nfdi )) ;

    // actualiser les dates
    ut.actime = stbuf->st_atime ;
    ut.modtime = stbuf->st_mtime ;
    CHK(utime(nfilei, &ut));
}


void recopie_repertoire( const char *rep, const char *filei, size_t taille)
{
    char nfilei [MAX_CHEMIN];
    struct stat stbuf ;

    // on récupère bname du fichier filei
    char *basec = strdup(filei); 
    char *bnamefilei = basename(basec);

    // on cree le nouveau chemin de nfilei
    creer_chemin(nfilei,rep, bnamefilei);
    
    // on récupère les droits et les permisions de filei
    CHK(lstat(filei, &stbuf));

    //on copie filei dans nfilei  
    copie_fichier( filei , nfilei, &stbuf,taille);
}



int main (int argc, const char *argv [])
{
    // vérification de usage
    if(argc < 4) 
        raler("usage : cprep taille rep f1 ... fn\n");

    // on recupere et verifie taille 
    size_t taille = atoi(argv[1]); 
    if (( int ) taille <= 0)
        raler("taille doit être positif\n");

    // on recupere le nb de fichier n
    int n = argc - 3 ;
    
    // créer le rep  s'il n'existe pas 
    const char * rep = argv[2];
    if (mkdir(rep, 0777) == -1 && errno != EEXIST)
        raler( "mkdir") ;

    // on recopie les fichiers dans rep
    for (int i = 1; i <= n; i++)
        recopie_repertoire( rep, argv[i+2],taille);

    exit(0);
}