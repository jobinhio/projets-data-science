import sys
from os.path import abspath

from functions import write_dataframe_to_excel
from functions import read_and_check_input, Separate_data, nettoyer_dataframe
from functions import construire_tableau, Transpose_dataframe
from functions import format_constraints_elements, format_constraints_qualite, format_constraints_MP
from functions import solve_linear_program
from functions import construct_result_dataframe

import pandas as pd
import numpy as np

def Test_conforme_contrainte(df_contraints_element,df_contraints_qualite,df_res):
    # Création d'un DataFrame df_conforme
    df_conforme = pd.DataFrame(columns=['Composant', 'Valeur'])

    n_ligne = df_res['Impurete'].idxmax()
    # Ajout des valeurs 'Impurete' et 'ONO' dans le DataFrame
    df_conforme.loc[0] = {'Composant': 'Impurete', 'Valeur': df_res.loc[n_ligne, 'Impurete'].round(2)}
    df_conforme.loc[1] = {'Composant': 'ONO', 'Valeur': df_res.loc[n_ligne, 'ONO'].round(3)}

    # Récupérer les valeurs minimales et maximales par four
    valeur_min_par_four = df_contraints_element['Valeur Min par four']
    valeur_max_par_four = df_contraints_element['Valeur Max par four']

    
    proportion_elements = df_res.loc[n_ligne, 'C':].tolist()
    # Convertir la série valeur_max_par_four en une liste de chaînes de caractères pour obtenir le nombre de décimales
    decimals = [len(str(val).split('.')[1]) for val in valeur_max_par_four]

    # Arrondir chaque valeur de proportion_elements en fonction du nombre de décimales correspondant
    proportion_elements = [round(val, num_decimals) for val, num_decimals in zip(proportion_elements, decimals)]


    # proportion_elements = [round(elem, 3) for elem in proportion_elements]


    # Ajout des valeurs des autres composants et calcul de la conformité
    for i, composant in enumerate(df_contraints_element['Composant'].tolist()):
        df_conforme.loc[i + 2, 'Composant'] = composant
        df_conforme.loc[i + 2, 'Valeur'] = proportion_elements[i]
    
    # Conditions de conformité
    impurete_valeur = df_conforme.loc[0, 'Valeur']
    impurete_min = df_contraints_qualite.loc[0, 'Impurété']
    impurete_max = df_contraints_qualite.loc[2, 'Impurété']
    condition1 = (impurete_min <= impurete_valeur <= impurete_max) or pd.isnull(impurete_min) or pd.isnull(impurete_max)


    Ono_valeur = df_conforme.loc[1, 'Valeur']
    Ono_min = df_contraints_qualite.loc[0, 'ONO']
    Ono_max = df_contraints_qualite.loc[2, 'ONO']
    condition2 = (Ono_min <= Ono_valeur <= Ono_max) or pd.isnull(Ono_min) or pd.isnull(Ono_max)

    # Récupérer les valeurs minimales et maximales par four
    valeur_min_par_four = df_contraints_element['Valeur Min par four']
    valeur_max_par_four = df_contraints_element['Valeur Max par four']
    condition3 = ((valeur_min_par_four <= proportion_elements) | valeur_min_par_four.isnull()) & \
                ((valeur_max_par_four >= proportion_elements) | valeur_max_par_four.isnull())

    condition = np.concatenate(([condition1, condition2], condition3.tolist()))

    # Ajout de la colonne 'Conforme ?' au DataFrame
    df_conforme['Conforme ?'] = np.where(condition, 1, 0)
    conforme = (df_conforme['Conforme ?'] == 1).all()
    print(df_conforme)
    return conforme,df_conforme

import os

def supprimer_fichier_resultats(chemin_fichier):
    # Créer le chemin complet du nouveau fichier Excel pour les résultats
    dossier_data = os.path.dirname(chemin_fichier)
    fichier_Resultats = os.path.join(dossier_data, 'Resultats.xlsx')

    # Vérifier si le fichier Excel existe déjà
    if os.path.exists(fichier_Resultats):
        # Supprimer le fichier existant
        os.remove(fichier_Resultats)

def sauvegarder_erreurs(message, chemin_fichier):
    erreurs = []
    erreurs.append(message)
    # Créer le chemin complet du nouveau fichier texte pour les erreurs
    dossier_data = os.path.dirname(chemin_fichier)
    fichier_erreurs = os.path.join(dossier_data, 'erreurs.txt')

    with open(fichier_erreurs, "w", encoding="utf-8") as f:
        for erreur in erreurs:
            f.write(erreur + "\n")
    print("Les erreurs ont été enregistrées dans le fichier '{}'.".format(fichier_erreurs))

def create_optimal_recipe(chemin_fichier):
    # Lire les fichiers Excel
    df_table, df_MP, df_contraints, erreurs = read_and_check_input(chemin_fichier)

    if len(erreurs) != 0 :
        return 0
    df_contraints_element, df_contraints_qualite, df_MP_dispo, df_MP_indispo = Separate_data(df_table, df_MP, df_contraints)

    # Suppression des matières premières indisponibles
    df_table = nettoyer_dataframe(df_table, df_MP_indispo)

    # Construction de la matrice A et du vecteur C
    A, C = construire_tableau(df_table, df_MP_dispo)

    # Initialisation des listes pour les contraintes
    A_ub, b_ub, A_eq, b_eq = [], [], [], []

    df_contraints_element = Transpose_dataframe(df_contraints_element)
    # Mettre  les contraintes concernant les éléments
    A_ub, b_ub, A_eq, b_eq = format_constraints_elements(A_ub, b_ub, A_eq, b_eq, df_contraints_element, A)


    # Mettre  les contraintes concernant la qualité
    A_ub, b_ub, A_eq, b_eq = format_constraints_qualite(A_ub, b_ub, A_eq, b_eq, df_contraints_qualite, A)


    # Mettre les contraintes concernant les matières premières disponibles
    A_eq, b_eq, bounds = format_constraints_MP(A_eq, b_eq, df_MP_dispo)


    # Résoudre le problème d'optimisation linéaire
    res = solve_linear_program(C, A_ub, b_ub, A_eq, b_eq, bounds)

    # if res.x.any() != None :
    # if res.x != None :
    if res.success:
        # Construire le DataFrame résultant
        df_res = construct_result_dataframe(df_MP_dispo, df_table, res)
        conforme,df_conforme = Test_conforme_contrainte(df_contraints_element,df_contraints_qualite,df_res)
        if conforme:
            # Écrire le DataFrame résultant dans le fichier Excel
            write_dataframe_to_excel(df_res, chemin_fichier, new_sheet_name='Recette')
        else :
            message = "Erreur : Veillez revoir les contraintes de la feuille 'Contraintes Qualités et Elément'"
            sauvegarder_erreurs(message, chemin_fichier)
            # supprimer_fichier_resultats(chemin_fichier)
            write_dataframe_to_excel(df_res, chemin_fichier, new_sheet_name='Recette')

            # Chemin du fichier erreurs.txt
            dossier_data = os.path.dirname(chemin_fichier)
            fichier_erreurs = os.path.join(dossier_data, 'erreurs.txt')

            # Écrire le contenu du DataFrame dans le fichier erreurs.txt
            with open(fichier_erreurs, 'a') as file_txt:
                file_txt.write("\n")
                df_conforme.to_csv(file_txt, sep='\t', index=False)
            return df_res
    else :
        print("Le problème n'admet pas de solution.")
    return res

# Appel de la fonction main avec le chemin du fichier Excel comme argument
if __name__ == "__main__":
    # Vérifiez si un chemin de fichier Excel est fourni en argument
    if len(sys.argv) != 2:
        print("Usage: python main.py chemin_vers_fichier_excel")
        sys.exit(1)

    # Récupérez le chemin du fichier Excel à partir des arguments de ligne de commande
    chemin_fichier_excel = abspath(sys.argv[1])

    # Appelez la fonction create_optimal_recipe avec le chemin du fichier Excel
    create_optimal_recipe(chemin_fichier_excel)