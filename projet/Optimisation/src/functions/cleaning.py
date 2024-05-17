import pandas as pd
import os


def Separate_data(df_table, df_MP, df_contraints): 
    # Récupérer les Elements chimiques
    Elements = list(df_table.columns)

    # Supprimer 'Article' si elle apparait dans Elements
    if 'Article' in Elements:
        Elements.remove('Article')
    if 'Code Article' in Elements:
        Elements.remove('Code Article')

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

    return df_contraints_element, df_contraints_qualite, df_MP_dispo, df_MP_indispo


def nettoyer_dataframe(df_table,  df_MP_indispo):
    """
    Supprime les lignes correspondant aux articles indisponibles et les colonnes des éléments chimiques spécifiés.

    Args:
    df (DataFrame): Le dataframe contenant les données.
    articles_indisponibles (list): Liste des noms des articles indisponibles.
    elements_a_supprimer (list): Liste des noms des éléments chimiques à supprimer.

    Returns:
    DataFrame: Le dataframe modifié.
    """
    # Supprimer les lignes correspondant aux articles indisponibles
    articles_indisponibles = df_MP_indispo['Article'].to_list()
    df_table = df_table[~df_table['Article'].isin(articles_indisponibles)]

    # Réinitialiser les indices du dataframe
    df_table = df_table.reset_index(drop=True)

    return df_table
