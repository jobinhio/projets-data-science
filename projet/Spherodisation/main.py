import os
import pandas as pd
import numpy as np
import sys
from os.path import abspath

from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import Workbook
import gc

from tqdm import tqdm


Poid_metrique_Mg = 43 #(g/m)
Poid_metrique_fil = 418 #(g/m)
Percent_Mg_in_1m  = Poid_metrique_Mg/Poid_metrique_fil*100 # % de Mg dans 1 m 
Q_visee = 0.045 # % de Mg visée 
Longueur_total_fil = 4400 # Longueur fil foure (m) 
L = Q_visee/Percent_Mg_in_1m*Longueur_total_fil


# Récuperation des paramètres de chaque recette 
def Give_input_values_per_recipe(chemin_fichier) :
    # Lecture de la première feuille du fichier Excel : Tableau des inputs 
    df = pd.read_excel(chemin_fichier, engine='calamine')

    # Supprimer les lignes entièrement vides de df
    df_input = df.dropna(how='all').reset_index(drop=True)

    # Obtenir les valeurs de la première colonne sous forme de liste
    liste_des_recettes = df_input[df_input.columns[0]].tolist()

    # Insérer le nom de la colonne au début de la liste
    liste_des_recettes.insert(0, df_input.columns[0])

    # Obtenir les types de recettes uniques
    types_de_recettes = df_input[df_input.columns[0]].dropna().unique().tolist()

    # Ajouter le nom de la colonne à la liste des types de recettes
    types_de_recettes.append(df_input.columns[0])

    # Initialiser un dictionnaire pour les contraintes par recettes
    Parametres_par_recettes = {}

    # Parcourir la liste des recettes
    for idx, recette in enumerate(liste_des_recettes):
        # Vérifier si la recette est un type de recette
        if recette in types_de_recettes:
            # Ajouter les contraintes de la recette au dictionnaire
            Parametres_par_recettes[recette] = df_input.iloc[idx:idx+1, 1:].reset_index(drop=True)

    return df, Parametres_par_recettes

# Calcule de la longueur du fil fourré et de la quantité de Mg à utiliser
def calculate_wire_length(P,S,t,T,R,Mg,K,Q_visee) :
    """
    Calcule la longueur de fil foure (en m) à introduire dans la fonte pour obtenir du graphite spherodial.
    Args:
    P: Poids de fonte à traiter en Kg.
    S: Taux de souffre de la fonte de base en %.
    t: Temps de séjour en minutes prévu pour la fonte après traitement.
    T: Température (degrés Celsius) de la fonte au moment du traitement, mesurée au couple.
    R: Rendement en magnésium de l'opération en %.
    Mg: Taux en magnésium dans l'alliage en %.
    K: Quantité de magnésium résiduel nécessaire pour que le graphite soit sous forme sphéroïdal en %.
    Q_visee: Pourcentage de magnésium visée en g.

    Returns:
    Q_t: Quantité d'alliage au magnésium à utiliser en Kg.
    L: La longueur du fil fourré à utiliser en m.
    """
    Q_t = P * (0.76 * (S - 0.01) + K + t * 1e-3) * (T / 1450) ** 2 / (R * Mg / 100)

    Poid_metrique_Mg = 43 #(g/m)
    Poid_metrique_fil = 418 #(g/m) # Q_visee égal % de Mg visée 
    Longueur_total_fil = 4400 # Longueur Total du fil foure (m) 

    Percent_Mg_in_1m  = Poid_metrique_Mg/Poid_metrique_fil*100 # % de Mg dans 1 m 

    L = Q_visee/Percent_Mg_in_1m*Longueur_total_fil
    return Q_t,L


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

    # Récupération des paramètres de chaque recette 
    df_input, Parametres_par_recettes = Give_input_values_per_recipe(chemin_fichier)
    df_output = df_input.copy()
    Q_L_name = ['Quantité théorique d\'alliage au magnésium à utiliser', 'Longueur théorique du fil fourré à utiliser']
    df_output[''] = np.nan
    df_output[Q_L_name] = np.nan

    for recette, df in Parametres_par_recettes.items():
        Parametres_name = df.columns[1:]

        # Extraction des Variables
        P, S, t, T, R, Mg, K,Q = (pd.to_numeric(df[param].iloc[0], errors='coerce') for param in Parametres_name)

        # Calcul de la longueur du fil fourré et de la quantité de Mg à utiliser
        Q_t, L = calculate_wire_length(P, S, t, T, R, Mg, K,Q)

        if recette != df_output.columns[0]:
            index_recette = df_output.index[df_output[df_output.columns[0]] == recette].tolist()[0]
            df_output[Q_L_name[0]] = df_output[Q_L_name[0]].astype(object)
            df_output.loc[index_recette, Q_L_name[0]] = Q_L_name[0]
            df_output.loc[index_recette + 1, Q_L_name[0]] = Q_t

            df_output[Q_L_name[1]] = df_output[Q_L_name[1]].astype(object)
            df_output.loc[index_recette, Q_L_name[1]] = Q_L_name[1]
            df_output.loc[index_recette + 1, Q_L_name[1]] = L
        else:
            df_output.loc[0, Q_L_name[0]] = Q_t
            df_output[Q_L_name[1]] = df_output[Q_L_name[1]].astype(object)
            df_output.loc[0, Q_L_name[1]] = L

    export_result(df_output, dossier_courant )
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

