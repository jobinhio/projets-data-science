

def construire_tableau(df_table, df_MP_dispo):
    """
    Construit la matrice des pourcentages des éléments dans chaque matière première et récupère les prix des matières premières.
    
    Args:
    - df_table : DataFrame contenant les pourcentages des éléments dans chaque article
    - df_MP_dispo : DataFrame contenant les prix des matières premières
    
    Returns:
    - A : Tableau NumPy des pourcentages des éléments dans chaque matière première (transposé)
    - C : Tableau NumPy contenant les prix des matières premières
    """
    # Construction de A : le tableau des pourcentages des éléments dans chaque matière première
    df_A = df_table.drop(columns=['Article','Code Article'])
    A = df_A.to_numpy().T

    # Récupération des prix des matières premières
    df_C = df_MP_dispo['Prix']
    C = df_C.to_numpy()

    return A, C


def Transpose_dataframe(df):
    """
    Transpose le DataFrame, définissant la première colonne comme noms de colonnes,
    puis déplace les index dans une nouvelle colonne, et enfin supprime le nom de l'index.
    
    Args:
    - df: DataFrame à transposer
    
    Returns:
    - DataFrame Transposé
    """
    # Transposer le DataFrame et définir la première colonne comme noms de colonnes
    df_transposed = df.set_index(df.columns[0]).transpose()
    
    # Déplacer les index dans une nouvelle colonne
    df_transposed.reset_index(inplace=True)
    df_transposed = df_transposed.rename(columns={'index': df.columns[0]})
    
    # Supprimer le nom de l'index
    df_transposed = df_transposed.rename_axis(None, axis=1)
    
    return df_transposed


