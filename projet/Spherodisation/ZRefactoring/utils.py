# Pour calculer la longueur du fil fourré 
def calcul_quantite_mg(P,S,t,e,T,R,Mg,K) :
    """
    Calcule la Quantité d'alliage au magnésium (en Kg) à introduire dans la fonte pour obtenir du graphite spherodial.
    Args:
    P: Poids de fonte à traiter en Kg.
    S: Taux de souffre de la fonte de base en %.
    t: Temps de séjour en minutes prévu pour la fonte après traitement.
    T: Température (degrés Celsius) de la fonte au moment du traitement, mesurée au couple.
    R: Rendement en magnésium de l'opération en %.
    Mg: Taux en magnésium dans l'alliage en %.
    K: Quantité de magnésium résiduel nécessaire pour que le graphite soit sous forme sphéroïdal en %.

    Returns:
    Q: Quantité d'alliage au magnésium à utiliser en Kg.
    """
    Q = P * (0.76 * (S - 0.01) + K + t * e) * (T / 1450) ** 2 / (R * Mg / 100)

    return Q

def calcul_longueur_fil( PPT, S, temps_gs, TPT,
    R, masse_fil, masse_mg_fil, Mgmax, eP, 
    PFClimite, Mglimite ):

    # % de Mg à ajouter dans la poche de traitement pour obtenir le Mg maximal
    K = ( Mgmax*(PFClimite + PPT) - Mglimite*PFClimite )/ PPT

    # Masse de Mg à ajouter dans la poche de traitement pour obtenir le Mg maximal
    Mgfil = masse_mg_fil/masse_fil *100
    Q = calcul_quantite_mg(PPT,S,temps_gs,eP,TPT,R,Mgfil,K) # en Kg


    # Longueur de fil pour avoir la masse de Mg manquante
    L = Q / (masse_fil* 1e-3)   # en m

    return K, L




# Calcule du temps limite avant lancement prochain traitement
def calculer_temps_epuis_PFC(PFC):
    # Constantes dans ce programme
    global Mgmin, eC, PFCmin, temps_traitement, temps_serie
    global liste_masses_grappes_moules, liste_cadences_moule_par_heure, liste_quantites_moules_a_produire, temps_serie

    # Calcul de la fonte four consommable
    PFCconsommable = PFC - PFCmin

    # Initialisation du temps total
    temps_total = 0

    # Boucle sur chaque modèle de moules
    for i in range(len(liste_masses_grappes_moules)):
        masse_grappe_i = liste_masses_grappes_moules[i]
        cadence_moule_par_heure_i = liste_cadences_moule_par_heure[i]
        quantite_moules_a_produire_i = liste_quantites_moules_a_produire[i]

        # Calcul de la cadence de fonte en kg/min pour le modèle i
        cadence_fonte_i = (cadence_moule_par_heure_i / 60) * masse_grappe_i  # en kg/min
        
        # Fonte nécessaire pour produire tous les moules de ce modèle
        fonte_necessaire_i = quantite_moules_a_produire_i * masse_grappe_i

        if PFCconsommable >= fonte_necessaire_i:
            # Si la fonte est suffisante pour produire tous les moules
            temps_pour_produire_i = fonte_necessaire_i / cadence_fonte_i
            temps_total += temps_pour_produire_i
            PFCconsommable -= fonte_necessaire_i

            # Ajouter le temps de la série s'il y a d'autres modèles à produire
            if i < len(liste_masses_grappes_moules) - 1:
                temps_total += temps_serie
        else:
            # Si la fonte n'est pas suffisante, calcul du temps possible avec la fonte restante
            temps_possible = PFCconsommable / cadence_fonte_i
            temps_total += temps_possible
            break  # On arrête la boucle, car il n'y a plus de fonte

    return temps_total

def calcul_temps_limite(PFC, Mg):
    
    global Mgmin, eC, temps_traitement

    # Temps en minute admissible avant l'ajout dans le four de coulée
    # avant d'atteindre la fonte minimal (en Kg) dans le four de coulée
    temps_epuis_PFC = calculer_temps_epuis_PFC(PFC)
    delai_avt_traitement_fonte_four = temps_epuis_PFC - temps_traitement


    
    # Temps en minute admissible avant l'ajout dans le four de coulée
    # avant d'atteindre le pourcentage minimal (%) dans le four de coulée
    Mgconsommable = Mg - Mgmin
    temps_epuis_Mg = Mgconsommable/eC
    delai_avt_traitement_mg_four = temps_epuis_Mg - temps_traitement


    # Temps en minute avant de lancer le traitement (Du four de fusion au four de coulée)
    delai_avt_traitement = min(delai_avt_traitement_fonte_four, delai_avt_traitement_mg_four)
    tempslimite = temps_traitement + delai_avt_traitement
    # mise a jour de la masse mg avant ajout poche après consomation de mg
    Mgconsommer = tempslimite*eC
    Mgconsommer = (temps_traitement + delai_avt_traitement)*eC
    Mglimite = Mg - Mgconsommer



    # Mise à jour de la masse de fonte avant ajout dans le four après consommation pendant
    # temps_traitement + delai_avt_traitement
    PFCconsommer = 0
    for i in range(len(liste_masses_grappes_moules)):
        masse_grappe_i = liste_masses_grappes_moules[i]
        cadence_moule_par_heure_i = liste_cadences_moule_par_heure[i]
        quantite_moules_a_produire_i = liste_quantites_moules_a_produire[i]

        # Calcul de la cadence de fonte en kg/min pour le modèle i
        cadence_fonte_i = (cadence_moule_par_heure_i / 60) * masse_grappe_i  # en kg/min

        # Vérification du temps restant par rapport au temps nécessaire pour produire tous les moules de ce modèle
        temps_pour_produire_i = quantite_moules_a_produire_i / (cadence_fonte_i / masse_grappe_i)
        
        if tempslimite > temps_pour_produire_i:
            # Si le délai est supérieur au temps nécessaire, consommer toute la fonte pour ce modèle
            PFCconsommer += cadence_fonte_i * temps_pour_produire_i
            tempslimite -= temps_pour_produire_i

            if i < len(liste_masses_grappes_moules) - 1:
                tempslimite -= temps_serie
        else:
            # Sinon, consommer la fonte en fonction du temps restant
            PFCconsommer += cadence_fonte_i * tempslimite
            break

    PFClimite =  PFC - PFCconsommer


    return delai_avt_traitement, Mglimite, PFClimite
