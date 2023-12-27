#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

void usage (char *argv0)
{
    fprintf (stderr, "usage: %s [port]\n", argv0) ;
    exit (1) ;
}

void raler (char *msg)
{
    perror (msg) ;
    exit (1) ;
}

#define	MAXLEN	1024

void serveur (int in)
{
    int r ;
    char buf [MAXLEN] ;
    int n ;

    n = 0 ;
    while ((r = read (in, buf, MAXLEN)) > 0)
	n += r ;
    printf ("%d\n", n) ;
}




void traiter_requete(int in, char *requete)
{
    // Extraire le type de requête du premier octet
    char type = requete[0];

    // Pointeur pour parcourir la requête
    char *ptr = requete + 1;

    switch (type)
    {
        case 0: // Requête de lister les images présentes
        {
            // Traitement de la requête de listage
            // ...

            // Exemple de réponse : une liste de noms
            char liste_noms[] = {2, 'i', 'm', 'g', '1', 'i', 'm', 'g', '2'};
            write(in, liste_noms, sizeof(liste_noms));
            break;
        }
        case 1: // Requête de tester l'existence d'une image
        {
            // Extraire le nom de la requête
            int len = (unsigned char)*ptr;
            ptr++;
            char nom[len + 1];
            strncpy(nom, ptr, len);
            nom[len] = '\0';

            // Traitement de la requête de test d'existence
            // ...

            // Exemple de réponse : une erreur
            char erreur[] = {7, 'E', 'r', 'r', 'e', 'u', 'r'};
            write(in, erreur, sizeof(erreur));
            break;
        }
        case 2: // Requête d'envoyer une image vers le serveur
        {
            // Extraire le nom et le contenu de la requête
            int len_nom = (unsigned char)*ptr;
            ptr++;
            char nom[len_nom + 1];
            strncpy(nom, ptr, len_nom);
            nom[len_nom] = '\0';
            ptr += len_nom;

            int len_contenu = *((int *)ptr);
            ptr += sizeof(int);
            char contenu[len_contenu];
            strncpy(contenu, ptr, len_contenu);

            // Traitement de la requête d'envoi d'image
            // ...

            // Exemple de réponse : une erreur
            char erreur[] = {5, 'O', 'K'};
            write(in, erreur, sizeof(erreur));
            break;
        }
        case 3: // Requête de récupérer une image depuis le serveur
        {
            // Extraire le nom de la requête
            int len = (unsigned char)*ptr;
            ptr++;
            char nom[len + 1];
            strncpy(nom, ptr, len);
            nom[len] = '\0';

            // Traitement de la requête de récupération d'image
            // ...

            // Exemple de réponse : le nom et le contenu de l'image
            int len_reponse = 9 + strlen(nom) + 1 + sizeof(int) + 7;
            char reponse[len_reponse];
            reponse[0] = (unsigned char)(strlen(nom) + 1);
            strncpy(reponse + 1, nom, strlen(nom) + 1);
            *((int *)(reponse + 1 + strlen(nom) + 1)) = 7;
            strncpy(reponse + 1 + strlen(nom) + 1 + sizeof(int), "Contenu", 7);
            write(in, reponse, len_reponse);
            break;
        }
        case 4: // Requête de supprimer une image sur le serveur
        {
            // Extraire le nom de la requête
            int len = (unsigned char)*ptr;
            ptr++;
            char nom[len + 1];
            strncpy(nom, ptr, len);
            nom[len] = '\0';

            // Traitement de la requête de suppression d'image
            // ...

            // Exemple de réponse : une erreur
            char erreur[] = {6, 'D', 'e', 'l', 'e', 't', 'e'};
            write(in, erreur, sizeof(erreur));
            break;
        }
        default:
            // Type de requête non pris en charge
            break;
    }
}

void serveur (int in)
{
    int r;
    char buf[MAXLEN];
    int n;

    // Lire la requête du client
    n = read(in, buf, MAXLEN);

    if (n > 0)
    {
        // Traiter la requête
        traiter_requete(in, buf);
    }
    else if (n < 0)
    {
        // Erreur de lecture
        perror("read");
    }
}











int main (int argc, char *argv [])
{
    int s, sd, r ;
    struct sockaddr_in6 monadr, sonadr ;
    socklen_t salong ;
    int port, val ;
    char padr [INET6_ADDRSTRLEN] ;

    switch (argc)
    {
	case 1 :
	    port = 9000 ;
	    break ;
	case 2 :
	    port = atoi (argv [1]) ;
	    break ;
	default :
	    usage (argv [0]) ;
    }

    // Création de la socket IPv6
    s = socket (PF_INET6, SOCK_STREAM, 0) ;
    if (s == -1) raler ("socket") ;

    // Désactivation de l'exclusivité IPv6
    val = 0 ;
    r = setsockopt (s, IPPROTO_IPV6, IPV6_V6ONLY, &val, sizeof val) ;
    if (r == -1) raler ("setsockopt") ;

    // Configuration de l'adresse d'écoute du serveur
    memset (&monadr, 0, sizeof monadr) ;
    monadr.sin6_family = AF_INET6 ;
    monadr.sin6_port = htons (port) ;
    monadr.sin6_addr = in6addr_any ;
    r = bind (s, (struct sockaddr *) &monadr, sizeof monadr) ;
    if (r == -1) raler ("bind") ;

    // Mise en écoute de la socket
    r = listen (s, 5) ;
    if (r == -1) raler ("listen") ;

    // Acceptation d'une connexion entrante
    salong = sizeof sonadr ;
    sd = accept (s, (struct sockaddr *) &sonadr, &salong) ;
    if (sd == -1) raler ("accept") ;

    // Récupération de l'adresse IP du client connecté
    if (inet_ntop (AF_INET6, &sonadr.sin6_addr, padr, sizeof padr) == NULL)
	raler ("inet_ntop") ;
    printf ("Connexion depuis %s\n", padr) ;


    // Appel de la fonction serveur pour traiter les données du client
    serveur (sd) ;

    // Fermeture des sockets
    close (sd) ;
    close (s) ;

    exit (0) ;
}
