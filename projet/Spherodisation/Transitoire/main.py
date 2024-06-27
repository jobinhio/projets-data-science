import os
import pandas as pd
import numpy as np
import sys
from os.path import abspath

from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import Workbook
import gc

from sympy import symbols, Eq, solve

def calcul_K_res_et_longueur_fil(P1, P2, P3, K_visee, eC, temps_traitement, T, S, t, R, Mg, eP, masse_fil):
    """
    Calcule les quantités de magnésium résiduel et la longueur théorique du fil fourré à utiliser pour que le graphite soit sous forme sphéroïdal.
    Args:
    - P1, P2, P3 : Poids des différentes fontes à traiter en Kg
    - K_visee : Quantité cible de magnésium pour que le graphite soit sous forme sphéroïdal en %
    - eP : Quantité de magnésium perdue par minute de séjour de la fonte après traitement ( phénomène d'évanouissement ) dans la poche en %
    - eC : Quantité de magnésium perdue par minute de séjour de la fonte après traitement ( phénomène d'évanouissement ) dans le four de coullée en %
    - temps_traitement : Durée du traitement en minutes
    - T : Température de la fonte au moment du traitement en degrés Celsius (même pour T1, T2, T3)
    - S : Taux de soufre de la fonte de base en %
    - t : Temps de séjour prévu pour la fonte après traitement en minutes
    - R : Rendement en magnésium de l'opération en %.
    - Mg : Taux en magnésium dans l'alliage en %.
    - masse_fil : Masse métrique du fil en g/m
    Returns:
    - K1, K2, K3 : Quantités de magnésium résiduel nécessaires pour chaque lot de fonte en %
    """
    
    # Calcul des pertes de magnésium
    mg_perdu = temps_traitement * eC

    
    S1, S2, S3 = S, S, S
    T1, T2, T3 = T, T, T
    t1, t2, t3 = t, t, t


    # Déclaration des variables symboliques
    K1, K2, K3 = symbols('K1 K2 K3')
    Q_1 = P1 * (0.76*(S1 - 0.01) + K1 + t1 * eP) * ((T1 / 1450)**2) / (R * Mg / 100)
    Q_2 = P2 * (0.76*(S2 - 0.01) + K2 + t2 * eP) * ((T2 / 1450)**2) / (R * Mg / 100)
    Q_3 = P3 * (0.76*(S3 - 0.01) + K3 + t3 * eP) * ((T3 / 1450)**2) / (R * Mg / 100)


    # Définition des équations
    eq1 = Eq(Q_1,Q_2)
    eq2 = Eq(Q_1,Q_3)
    eq3 = Eq(K_visee * (P1 + P2 + P3),
            K1*P1*( 1 - 2*mg_perdu) + K2*P2*(1 - mg_perdu) + K3*P3)


    
    # Résolution du système d'équations
    solution = solve((eq1, eq2, eq3), (K1, K2, K3))
    
    # Récupération des résultats
    K1_res = float(solution[K1])
    K2_res = float(solution[K2])
    K3_res = float(solution[K3])

    # Apres l'ajout des poches
    pct_mg_coulee1 = K1_res
    pct_mg_coulee2 = (pct_mg_coulee1*(1 - temps_traitement * eC)*P1 + K2_res*P2)/(P1 + P2)
    pct_mg_coulee3 = (pct_mg_coulee2*(1 - temps_traitement * eC)*(P1 + P2) + K3_res*P3)/(P1 + P2 + P3)
    

    # pct_mg_coulee1 = K1_res
    # pct_mg_coulee2 = (pct_mg_coulee1*(1 - temps_traitement * eC)*P1 + K2_res*P2)/((1 - pct_mg_coulee1*temps_traitement * eC)*P1 + P2)
    # pct_mg_coulee3 = (pct_mg_coulee2*(1 - temps_traitement * eC)*(P1 + P2) + K3_res*P3)/((1 - pct_mg_coulee2*temps_traitement * eC)*(P1 + P2) + P3)
    
    # print(K1_res,K2_res,K3_res)
    # print(pct_mg_coulee1,pct_mg_coulee2,pct_mg_coulee3)

    # Longueur de fil pour avoir la masse de Mg manquante
    Q = P1 * (0.76*(S1 - 0.01) + K1_res + t1 * eP) * ((T1 / 1450)**2) / (R * Mg / 100)
    L = Q / (masse_fil* 1e-3)   # en m
    return K1_res, K2_res, K3_res, pct_mg_coulee1, pct_mg_coulee2, pct_mg_coulee3, L


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
    df = pd.read_excel(chemin_fichier, engine='openpyxl')

    # Supprimer les lignes vides
    df2 = df.dropna(how='all').reset_index(drop=True)

    # Extraction des paramètres Généraux de traitement GS
    pct_rendement_mg, masse_fil, masse_mg_fil, K_visee,pct_perdu_mg_coulee_min, pct_perdu_mg_poche_min, temps_traitement, temps_gs= [
        pd.to_numeric(df2.iloc[1, i], errors='coerce') for i in range(0, 8)
    ]
    # Extraction des variables du Fours de fusion
    pct_Soufre, tempera_fonte_poche = [
        pd.to_numeric(df2.iloc[4, i], errors='coerce') for i in range(3, 5)
    ]

    # Extraction des variables du Fours de couléee
    masse_fonte_poche_1, masse_fonte_poche_2, masse_fonte_poche_3 = [
        pd.to_numeric(df2.iloc[7, i], errors='coerce') for i in range(0, 3)
    ]
    pct_mg_fil = masse_mg_fil/masse_fil *100
    
    K1_res, K2_res, K3_res, pct_mg_coulee1, pct_mg_coulee2, pct_mg_coulee3, L = calcul_K_res_et_longueur_fil(masse_fonte_poche_1, masse_fonte_poche_2, masse_fonte_poche_3, 
                                                                K_visee, pct_perdu_mg_coulee_min, 
                                                                temps_traitement, tempera_fonte_poche, pct_Soufre, temps_gs, pct_rendement_mg, pct_mg_fil,pct_perdu_mg_poche_min, masse_fil)
            
    # Liste des noms de valeurs à rechercher
    output_name = [
        'Pourcentage de magnésium résiduel dans  la poche de traitement 1 (%)',
        'Pourcentage de magnésium résiduel dans  la poche de traitement 2 (%)',
        'Pourcentage de magnésium résiduel dans la poche de traitement 3 (%)',
        'Pourcentage de magnésium dans le four de coulée après l\'ajout poche 1 (%)',
        'Pourcentage de magnésium dans le four de coulée après l\'ajout poche 2 (%)',
        'Pourcentage de magnésium dans le four de coulée après l\'ajout poche 3 (%)',
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

    df_res = df.copy()

    df_res.loc[indices_lignes_output[0] +1, noms_colonnes_output[0]] = K1_res
    df_res.loc[indices_lignes_output[1] +1, noms_colonnes_output[1]] = K2_res
    df_res.loc[indices_lignes_output[2]+1, noms_colonnes_output[2]] = K3_res
    df_res.loc[indices_lignes_output[3]+1, noms_colonnes_output[3]] = pct_mg_coulee1
    df_res.loc[indices_lignes_output[4]+1, noms_colonnes_output[4]] = pct_mg_coulee2
    df_res.loc[indices_lignes_output[5]+1, noms_colonnes_output[5]] = pct_mg_coulee3
    df_res.loc[indices_lignes_output[6]+1, noms_colonnes_output[6]] = L

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

