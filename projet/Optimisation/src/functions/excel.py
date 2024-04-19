import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import os
from openpyxl import Workbook


def lire_fichiers_excel(chemin_fichier): 
    # Lecture de la première feuille du fichier Excel : Table Matière Element
    df_table = pd.read_excel(chemin_fichier, engine='calamine')
    # Lecture de la deuxième feuille du fichier Excel : Contraintes Element
    df_contraints = pd.read_excel(chemin_fichier, engine='calamine', sheet_name=1)
    # Lecture de la troisième feuille du fichier Excel : Contraintes Matière Première
    df_MP = pd.read_excel(chemin_fichier, engine='calamine', sheet_name=2)


    # Récupérer les Elements chimiques
    Elements = list(df_table.columns)

    # Supprimer 'Article' si elle apparait dans Elements
    if 'Article' in Elements:
        Elements.remove('Article')

    #  qualités + les Elements
    contraints = df_contraints.columns[:3].tolist() + Elements
    # On récupère les contraintes sur la qualité et les Elements
    df_contraints = df_contraints.loc[:, contraints]

    
    # Filtrage des articles disponibles et indisponibles
    df_MP_indispo = df_MP[df_MP['Disponible ?'] == 0].reset_index(drop=True)
    df_MP_dispo = df_MP[df_MP['Disponible ?'] == 1].reset_index(drop=True)

    # Separation des contraintes
    df_contraints_qualite = df_contraints.loc[:,['Composant','Impurété','ONO']]
    df_contraints_element = df_contraints.drop(columns=['Impurété', 'ONO'])

    return df_table,df_contraints_element, df_contraints_qualite, df_MP_dispo, df_MP_indispo



def write_dataframe_to_excel(df, excel_file_path, new_sheet_name='Recette'):
    """
    Écrit un DataFrame dans une nouvelle feuille Excel ou écrase une feuille existante avec les données du DataFrame.

    Args:
        df (DataFrame): Le DataFrame à écrire dans le fichier Excel.
        excel_file_path (str): Chemin du fichier Excel existant.
        new_sheet_name (str, optional): Nom de la nouvelle feuille Excel. Par défaut, 'Recette'.

    Returns:
        None
    """


    workbook = Workbook()

    # Supprimer la première feuille s'il y en a une
    if workbook.sheetnames:
        first_sheet = workbook.sheetnames[0]
        workbook.remove(workbook[first_sheet])


    # Vérifier si la feuille existe déjà dans le classeur Excel
    if new_sheet_name in workbook.sheetnames:
        # Si la feuille existe déjà, effacer les données
        workbook.remove(workbook[new_sheet_name])

    # Ajouter la nouvelle feuille au classeur Excel
    workbook.create_sheet(title=new_sheet_name)

    # Charger la feuille nouvellement créée
    new_sheet = workbook[new_sheet_name]

    # Écrire les données dans la feuille
    for row in dataframe_to_rows(df, index=False, header=True):
        new_sheet.append(row)

    # Créer le chemin complet du nouveau fichier Excel
    dossier_parent = os.path.dirname(excel_file_path)
    nouveau_fichier_excel = os.path.join(dossier_parent, 'Resultats.xlsx')

    # Sauvegarder le classeur Excel dans le nouveau fichier Excel
    workbook.save(nouveau_fichier_excel)

    # Fermer le classeur Excel
    workbook.close()