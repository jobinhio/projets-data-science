import os
import pandas as pd
import numpy as np
import sys
from os.path import abspath

from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import Workbook
import gc

from tqdm import tqdm

# Calcule la quantité de Mg à utiliser
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

# Calcule de la longueur du fil fourré et de la masse de fonte limite dans le four de maintien
def calcul_longueur_fil_et_limite_four(
    masse_grappe, nb_moules_heure, masse_fonte_poche, masse_fonte_coulee, pct_mg_fonte_coulee,
    pct_Soufre, tempera_fonte_poche,
    pct_rendement_mg, masse_fil, masse_mg_fil, masse_fonte_coulee_min, masse_fonte_coulee_max, pct_mg_fonte_coulee_min,
    pct_mg_fonte_coulee_max, pct_perdu_mg_coulee_min, pct_perdu_mg_poche_min, temps_traitement, temps_gs,
    heure_lancement):

    # Temps en minute admissible avant l'ajout dans le four de maintien
    # avant d'atteindre la fonte minimal (en Kg) dans le four de maintien
    consommation_fonte_min = nb_moules_heure * masse_grappe / 60  # en kg/min
    fonte_four_consommable = masse_fonte_coulee - masse_fonte_coulee_min
    temps_epuis_fonte = fonte_four_consommable/consommation_fonte_min
    delai_avt_traitement_fonte_four = temps_epuis_fonte - temps_traitement



    # Temps en minute admissible avant l'ajout dans le four de maintien
    # avant d'atteindre le pourcentage minimal (%) dans le four de maintien
    pct_mg_four_consommable = pct_mg_fonte_coulee - pct_mg_fonte_coulee_min
    temps_epuis_mg = pct_mg_four_consommable/pct_perdu_mg_coulee_min
    delai_avt_traitement_mg_four = temps_epuis_mg - temps_traitement


    # Temps en minute avant de lancer le traitement (Du four de fusion au four de maintien)
    delai_avt_traitement = min(delai_avt_traitement_fonte_four, delai_avt_traitement_mg_four)

    # print(delai_avt_traitement_fonte_four, delai_avt_traitement_mg_four)
    # mise a jour de la masse fonte avant ajout poche mais après consomation de la fonte
    masse_fonte_four_consommer = (temps_traitement + delai_avt_traitement)*consommation_fonte_min 
    masse_four_limite =  masse_fonte_coulee - masse_fonte_four_consommer


    # mise a jour de la masse mg avant ajout poche après consomation de mg
    pct_mg_four_consommer = (temps_traitement + delai_avt_traitement)*pct_perdu_mg_coulee_min
    pct_mg_four_limite = pct_mg_fonte_coulee - pct_mg_four_consommer


    # % de Mg à ajouter dans la poche de traitement pour obtenir le Mg maximal
    K = ( pct_mg_fonte_coulee_max*(masse_four_limite + masse_fonte_poche) - pct_mg_four_limite*masse_four_limite )/ masse_fonte_poche

    # Masse de Mg à ajouter dans la poche de traitement pour obtenir le Mg maximal
    pct_mg_fil = masse_mg_fil/masse_fil *100
    Q = calcul_quantite_mg(masse_fonte_poche,pct_Soufre,temps_gs,pct_perdu_mg_poche_min,tempera_fonte_poche,pct_rendement_mg,pct_mg_fil,K) # en Kg


    # Longueur de fil pour avoir la masse de Mg manquante
    longueur_fil_necessaire = Q / (masse_fil* 1e-3)   # en m

    return K,delai_avt_traitement,pct_mg_four_limite,masse_four_limite,longueur_fil_necessaire

def Calcule_Temps_prochain_traitement(delai_avt_traitement,heure_lancement):
    # Trouver les positions des unités de temps dans la chaîne
    pos_hr = heure_lancement.find('hr')
    pos_min = heure_lancement.find('min')
    pos_sec = heure_lancement.find('s')

    # Extraire les valeurs numériques
    now_hours = int(heure_lancement[:pos_hr].strip()) 
    now_minutes = int(heure_lancement[pos_hr+3:pos_min].strip()) 
    now_seconds = int(heure_lancement[pos_min+4:pos_sec].strip()) 


    # Calculer le temps total en secondes
    total_seconds = now_hours * 3600 + now_minutes * 60 + now_seconds + delai_avt_traitement*60

    # Calculer les nouvelles heures, minutes et secondes
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)

    heure_prochain_lancement = f"{hours} hr {minutes} min {seconds} s"
    return heure_prochain_lancement

def export_result(df, dossier_data):
    """
    """
    # Créer le chemin complet du nouveau fichier Excel
    fichier_resultats = os.path.join(dossier_data, 'Resultats.xlsx')

    workbook = Workbook()
    feuille = workbook.active 

    # Écrire le DataFrame dans la feuille
    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            feuille.cell(row=r_idx, column=c_idx, value=value)

    # Sauvegarder le classeur
    workbook.save(fichier_resultats)
    workbook.close()
    gc.collect()
    return 

def main_fct(chemin_fichier, dossier_courant):
    # Lecture de la première feuille du fichier Excel
    df = pd.read_excel(chemin_fichier, engine='calamine')#'openpyxl')
    # Supprimer les lignes vides
    df2 = df.dropna(how='all').reset_index(drop=True)

    # Extraction des paramètres Généraux de traitement GS
    pct_rendement_mg, masse_fil, masse_mg_fil, masse_fonte_coulee_min, masse_fonte_coulee_max, pct_mg_fonte_coulee_min= [
        pd.to_numeric(df2.iloc[1, i], errors='coerce') for i in range(0, 6)
    ]

    pct_mg_fonte_coulee_max, pct_perdu_mg_coulee_min, pct_perdu_mg_poche_min, temps_traitement, temps_gs = [
        pd.to_numeric(df2.iloc[1, i], errors='coerce') for i in range(6, 11)
    ]

    heure_lancement = df2.iloc[1, 11]

    # Extraction des variables du Fours de fusion
    pct_Soufre, tempera_fonte_poche = [
        pd.to_numeric(df2.iloc[4, i], errors='coerce') for i in range(5, 7)
    ]

    # Extraction des variables du Fours de couléee
    masse_grappe, nb_moules_heure, masse_fonte_poche, masse_fonte_coulee, pct_mg_fonte_coulee = [
        pd.to_numeric(df2.iloc[7, i], errors='coerce') for i in range(0, 5)
    ]


    # Calcul de la longueur de fil nécessaire
    K,delai_avt_traitement,pct_mg_fonte_coulee_limite,masse_fonte_coulee_limite,longueur_fil_necessaire = calcul_longueur_fil_et_limite_four(
            masse_grappe, nb_moules_heure, masse_fonte_poche, masse_fonte_coulee, pct_mg_fonte_coulee,
        pct_Soufre, tempera_fonte_poche,
        pct_rendement_mg, masse_fil, masse_mg_fil, masse_fonte_coulee_min, masse_fonte_coulee_max, pct_mg_fonte_coulee_min,
        pct_mg_fonte_coulee_max, pct_perdu_mg_coulee_min, pct_perdu_mg_poche_min, temps_traitement, temps_gs,
        heure_lancement)
        
    # Liste des noms de valeurs à rechercher
    output_name = [
        'Pourcentage de magnésium dans le four de coulée au moment de l\'ajout de la poche (%)',
        'Masse de la fonte dans le four de coulée au moment de l\'ajout de la poche (en Kg)',
        'Pourcentage de magnésium dans le four de coulée après  l\'ajout de la poche (%)',
        'Masse de la fonte dans le four de coulée  après l\'ajout de la poche (en Kg)',
        'Temps restant avant le lancement du prochain traitement (en seconde)',
        'Heure de lancement du prochain traitement',
        'Longueur théorique du fil fourré à utiliser (en m)'

    ]

    # Listes pour stocker les résultats
    indices_lignes_output = []
    noms_colonnes_output = []

    # Parcours du DataFrame pour trouver chaque valeur spécifique
    for target_value in output_name:
        found = False
        for index, row in df.iterrows():
            for col_name in df.columns:
                if row[col_name] == target_value:
                    indices_lignes_output.append(index)
                    noms_colonnes_output.append(col_name)
                    found = True
                    break
            if found:
                break


    heure_prochain_lancement = Calcule_Temps_prochain_traitement(delai_avt_traitement,heure_lancement)
    df_res = df.copy()

    masse_mg_coulee = pct_mg_fonte_coulee_limite* masse_fonte_coulee_limite/100  
    masse_mg_poche = K*masse_fonte_poche/100  
    pct_mg_coulee_apres_ajout = (masse_mg_coulee+masse_mg_poche)/(masse_fonte_coulee_limite+masse_fonte_poche)*100
    # df_res.columns.values[10:12] = res_name
    df_res.loc[indices_lignes_output[0] +1, noms_colonnes_output[0]] = pct_mg_fonte_coulee_limite
    df_res.loc[indices_lignes_output[1] +1, noms_colonnes_output[1]] = masse_fonte_coulee_limite
    df_res.loc[indices_lignes_output[2]+1, noms_colonnes_output[2]] = pct_mg_coulee_apres_ajout
    df_res.loc[indices_lignes_output[3]+1, noms_colonnes_output[3]] = masse_fonte_coulee_limite+masse_fonte_poche
    df_res.loc[indices_lignes_output[4]+1, noms_colonnes_output[4]] = delai_avt_traitement
    df_res.loc[indices_lignes_output[5]+1, noms_colonnes_output[5]] = heure_prochain_lancement
    df_res.loc[indices_lignes_output[6]+1, noms_colonnes_output[6]] = longueur_fil_necessaire

    export_result(df_res, dossier_courant )
    return 

if __name__ == "__main__":
    # Vérifiez si un chemin de fichier Excel est fourni en argument
    if len(sys.argv) != 2:
        print("Usage: python main.py recipe_optimization_data")
        sys.exit(1)
    # Récupérez le chemin du fichier Excel à partir des arguments de ligne de commande
    chemin_fichier = abspath(sys.argv[1])

    # On recupere le chemin du dossier data
    dossier_courant = os.path.dirname(chemin_fichier)
    # Solve problème
    main_fct(chemin_fichier, dossier_courant)

