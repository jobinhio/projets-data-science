import pandas as pd
import os


def Separate_data(df_table_mp, df_mp, df_elmt_and_quality): 
    """
    Sépare les données en contraintes sur les éléments et la qualité, les matières premières disponibles et indisponibles.

    Args:
    df_table_mp (DataFrame): DataFrame contenant les données sur les matières premières.
    df_mp (DataFrame): DataFrame contenant les données sur les matières premières avec disponibilité.
    df_elmt_and_quality (DataFrame): DataFrame contenant les contraintes sur les éléments et la qualité.

    Returns:
    DataFrame: DataFrame contenant les contraintes sur les éléments.
    DataFrame: DataFrame contenant les contraintes sur la qualité.
    DataFrame: DataFrame contenant les matières premières disponibles.
    DataFrame: DataFrame contenant les matières premières indisponibles.
    """
    # Récupérer les Elements chimiques
    Elements = list(df_table_mp.columns)

    # Supprimer 'Article' si elle apparait dans Elements
    if 'Article' in Elements:
        Elements.remove('Article')
    if 'Code Article' in Elements:
        Elements.remove('Code Article')

    #  qualités + les Elements
    contraints = df_elmt_and_quality.columns[:3].tolist() + Elements
    # On récupère les contraintes sur la qualité et les Elements
    df_elmt_and_quality = df_elmt_and_quality.loc[:, contraints]

    
    # Filtrage des articles disponibles et indisponibles
    df_mp_indispo = df_mp[df_mp['Disponible ?'] == 0].reset_index(drop=True)
    df_mp_dispo = df_mp[df_mp['Disponible ?'] == 1].reset_index(drop=True)

    # Separation des contraintes
    df_contraints_qualite = df_elmt_and_quality.loc[:,['Composant','Impurété','ONO']]
    df_contraints_element = df_elmt_and_quality.drop(columns=['Impurété', 'ONO'])

    return df_contraints_element, df_contraints_qualite, df_mp_dispo, df_mp_indispo


def clean_table_mp(df_table_mp, df_mp_indispo):
    """
    Supprime les lignes correspondant aux articles indisponibles du DataFrame des matières premières.
    
    Args:
    df_table_mp (DataFrame): Le DataFrame contenant les données sur les matières premières.
    df_mp_indispo (DataFrame): Le DataFrame contenant les données sur les matières premières indisponibles.
    
    Returns:
    DataFrame: Le DataFrame modifié après nettoyage.
    """
    # Supprimer les lignes correspondant aux articles indisponibles
    articles_indisponibles = df_mp_indispo['Article'].to_list()
    df_table_mp = df_table_mp[~df_table_mp['Article'].isin(articles_indisponibles)]

    # Réinitialiser les indices du dataframe
    df_table_mp = df_table_mp.reset_index(drop=True)

    return df_table_mp
