import pandas as pd
import numpy as np
import os
from .constants import Impurete_Values, ONO_Values
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl import Workbook
import gc


def remove_old_resultats(dossier_data):
    gc.collect()
    # Vérifier si le fichier résultats existe et le supprime
    fichier_resultats = os.path.join(dossier_data, 'Resultats.xlsx')
    if os.path.exists(fichier_resultats):
        os.remove(fichier_resultats)

    # Vérifier si le fichier erreurs existe et le supprime
    fichier_erreurs = os.path.join(dossier_data, 'erreurs.txt')
    if os.path.exists(fichier_erreurs):
        os.remove(fichier_erreurs)
    return 


def construct_result_dataframe(res, df_MP_dispo, raw_material_table, constraints):
    # Constantes pour les seuils
    SEUIL_0 = 1e-20
    SEUIL_1 = 1e-20  # 0.01

    # Création du DataFrame df_res
    df_res = df_MP_dispo[['Code Article','Article', 'Prix', 'Métallique ?']].copy()

    # Ajout de la colonne 'Proportion' avec les valeurs de res.x
    df_res['Proportion'] = res.x

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
    elements_selectionnes = raw_material_table[raw_material_table['Article'].isin(articles_selectionnes)]
    df_res = pd.merge(df_res, elements_selectionnes, on=['Code Article','Article'], how='inner')

    # Ajout de la ligne de résultats
    df_res.loc[df_res.shape[0] , :] = np.nan
    df_res.loc[df_res.shape[0] , 'Article'] = 'Resultats'

    df_res.loc[df_res.shape[0] - 1, ['Proportion', 'Valeur (/T)']] = [df_res['Proportion'].sum(), df_res['Valeur (/T)'].sum()]

    # Calcul des proportions des éléments dans la fonte
    cols_elements = raw_material_table.columns[2:]
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

    # Ajout du resultats des contraintes de MP
    b_eq = constraints['b_eq'] 
    for key, value in b_eq.items() :
        for article in df_res['Article'] :
            if article == key :
                contraints_res[key] = df_res.loc[df_res['Article'] == key,'Proportion'].values[0]
    return df_res,contraints_res


def export_result(df, dossier_data, new_sheet_name):
    # Créer le chemin complet du nouveau fichier Excel
    fichier_resultats = os.path.join(dossier_data, 'Resultats.xlsx')

    # Vérifier si le fichier Excel existe
    if os.path.exists(fichier_resultats):
        # Charger le classeur Excel existant
        workbook = load_workbook(fichier_resultats)
        feuille = workbook.create_sheet(title=new_sheet_name)

    # Créer un nouveau classeur s'il n'existe pas
    else:
        workbook = Workbook()
        feuille = workbook.active 
        feuille.title = new_sheet_name

    # Écrire le DataFrame dans la feuille
    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            feuille.cell(row=r_idx, column=c_idx, value=value)

    # Sauvegarder le classeur
    workbook.save(fichier_resultats)
    workbook.close()
    return 


def save_errors(erreurs, dossier_data,recette):
    # Sauvegarder les erreurs dans un fichier texte
    fichier_erreurs = os.path.join(dossier_data, 'erreurs.txt')
    with open(fichier_erreurs, "a+", encoding="utf-8") as f:
        message = "Sur la recette " + recette + ":"
        f.write(message+ "\n")
        for erreur in erreurs:
            f.write(erreur + "\n")
        f.write("\n")
    return 


