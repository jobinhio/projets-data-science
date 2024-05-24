import pandas as pd
import numpy as np
import os
from .constants import Impurete_Values, ONO_Values
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import Workbook
import gc


def remove_old_recipes(dossier_data):
    """
    Supprime les anciens fichiers de recettes et de fichiers d'erreurs, s'ils existent, dans le dossier de données.

    Args:
    dossier_data (str): Chemin vers le dossier contenant les données.

    Returns:
    None
    """
    gc.collect()
    # Vérifier si le fichier résultats existe et le supprime
    fichier_recipes = os.path.join(dossier_data, 'recipes.xlsx')
    if os.path.exists(fichier_recipes):
        os.remove(fichier_recipes)

    # Vérifier si le fichier erreurs existe et le supprime
    fichier_erreurs = os.path.join(dossier_data, 'erreurs.txt')
    if os.path.exists(fichier_erreurs):
        os.remove(fichier_erreurs)
    return 


def construct_result_dataframe(res, df_mp_dispo, table_mp, constraints):
    """
    Construit un DataFrame contenant les résultats de l'optimisation ainsi que les contraintes à respecter.

    Args:
    res: Résultat de l'optimisation.
    df_mp_dispo (DataFrame): DataFrame contenant les données sur les matières premières disponibles.
    table_mp (DataFrame): DataFrame contenant les données sur les matières premières et leurs éléments.
    constraints (dict): Dictionnaire contenant les contraintes du problème.

    Returns:
    DataFrame: DataFrame contenant les résultats de l'optimisation.
    dict: Dictionnaire contenant les contraintes du résultat.
    """
    # Constantes pour les seuils Métalliques
    SEUIL_0 = 1e-20
    SEUIL_1 = 1e-20  # 0.01

    # Création du DataFrame df_res
    df_res = df_mp_dispo[['Code Article','Article', 'Prix', 'Métallique ?']].copy()

    # Ajout de la colonne 'Proportion' avec les valeurs de res.x
    # df_res['Proportion'] = res.x
    df_res['Proportion'] = res.x[:df_mp_dispo[['Prix']].shape[0]]

    # Calcul de la colonne 'Valeur (/T)' en multipliant 'Proportion' par 'Prix'
    df_res['Valeur (/T)'] = df_res['Proportion'] * df_res['Prix']

    # Filtre des lignes avec des proportions non nulles seulement
    df_res = df_res[df_res['Proportion'] > 0]

    # Tri du DataFrame par 'Proportion' de manière décroissante
    df_res.sort_values(by='Proportion', ascending=False, inplace=True)

    # Initialisation des colonnes 'ONO' et 'Impurete' avec des valeurs NaN
    df_res['ONO'] = np.nan
    df_res['Impurete'] = np.nan

    # Filtrage des lignes en fonction de la valeur de la colonne 'Métallique ?' et du seuil correspondant
    df_res = df_res.loc[((df_res['Métallique ?'] == 0) & (df_res['Proportion'] >= SEUIL_0)) |
                        ((df_res['Métallique ?'] == 1) & (df_res['Proportion'] >= SEUIL_1))]

    # Suppression de la colonne 'Métallique ?' qui n'est plus nécessaire
    df_res.drop(columns=['Métallique ?'], inplace=True)

    # Fusion avec les éléments chimiques correspondant aux articles sélectionnés
    articles_selectionnes = df_res['Article'].tolist()
    elements_selectionnes = table_mp[table_mp['Article'].isin(articles_selectionnes)]
    df_res = pd.merge(df_res, elements_selectionnes, on=['Code Article','Article'], how='inner')

    # Ajout de la ligne de résultats
    df_res.loc[df_res.shape[0] , :] = np.nan
    df_res.loc[df_res.shape[0] , 'Article'] = 'Résultats'

    df_res.loc[df_res.shape[0] - 1, ['Proportion', 'Valeur (/T)']] = [df_res['Proportion'].sum(), df_res['Valeur (/T)'].sum()]

    # Calcul des proportions des éléments dans la fonte
    cols_elements = table_mp.columns[2:]
    proportions_elements = df_res[cols_elements].mul(df_res['Proportion'], axis=0).sum()

    # Ajout des valeurs des proportions des éléments
    df_res.loc[df_res.shape[0]-1, cols_elements] = proportions_elements 

    # Calcul des valeurs des indicateurs qualité
    impurete_values, ono_values = np.array(list(Impurete_Values.values())), np.array(list(ONO_Values.values()))
    df_res.loc[df_res.shape[0]-1, 'Impurete'] = impurete_values @ proportions_elements
    df_res.loc[df_res.shape[0]-1, 'ONO'] = ono_values @ proportions_elements

    contraints_res = {}
    contraints_res = proportions_elements.to_dict()
    contraints_res['Impurete'] = impurete_values @ proportions_elements
    contraints_res['ONO'] = ono_values @ proportions_elements
    contraints_res['Proportion_Total'] = df_res.loc[df_res.shape[0] - 1, ['Proportion']].values[0]

    # Ajout du recipes des contraintes de MP
    b_eq = constraints['b_eq'] 
    for key, value in b_eq.items() :
        for article in df_res['Article'] :
            if article == key :
                contraints_res[key] = df_res.loc[df_res['Article'] == key,'Proportion'].values[0]
    return df_res,contraints_res


def export_result(df_res, dossier_data, new_sheet_name):
    """
    Exporte un DataFrame dans un fichier Excel, créant une nouvelle feuille ou mettant à jour une feuille existante.

    Args:
    df_res (DataFrame): Le DataFrame à exporter.
    dossier_data (str): Chemin vers le dossier contenant les données.
    new_sheet_name (str): Nom de la nouvelle feuille Excel.

    Returns:
    None
    """
    # Créer le chemin complet du nouveau fichier Excel
    fichier_recipes = os.path.join(dossier_data, 'recipes.xlsx')

    # Vérifier si le fichier Excel existe
    if os.path.exists(fichier_recipes):
        # Charger le classeur Excel existant
        workbook = load_workbook(fichier_recipes)
        feuille = workbook.create_sheet(title=new_sheet_name)

    # Créer un nouveau classeur s'il n'existe pas
    else:
        workbook = Workbook()
        feuille = workbook.active 
        feuille.title = new_sheet_name

    # Écrire le DataFrame dans la feuille
    for r_idx, row in enumerate(dataframe_to_rows(df_res, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            feuille.cell(row=r_idx, column=c_idx, value=value)

    # Sauvegarder le classeur
    workbook.save(fichier_recipes)
    workbook.close()
    gc.collect()
    return 


def save_errors(erreurs, dossier_data,recette):
    """
    Sauvegarde les erreurs dans un fichier texte.

    Args:
    erreurs (list): Liste des erreurs à sauvegarder.
    dossier_data (str): Chemin vers le dossier contenant les données.
    recette (str): Nom de la recette associée aux erreurs.

    Returns:
    None
    """
    # Sauvegarder les erreurs dans un fichier texte
    fichier_erreurs = os.path.join(dossier_data, 'erreurs.txt')
    with open(fichier_erreurs, "a+", encoding="utf-8") as f:
        message = "Pour la recette " + recette + ":"
        f.write(message+ "\n")
        for erreur in erreurs:
            f.write(erreur + "\n")
        f.write("\n")
    return 


