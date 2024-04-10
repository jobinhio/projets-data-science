

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