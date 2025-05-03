import numpy as np
import pandas as pd
from .constants import Impurete_Values, ONO_Values

def create_matrix_A_and_C(table_mp, df_mp_dispo):
    """
    Construit la matrice des pourcentages des éléments dans chaque matière première et récupère les prix des matières premières.
    
    Args:
    - table_mp : DataFrame contenant les pourcentages des éléments dans chaque article
    - df_mp_dispo : DataFrame contenant les prix des matières premières disponibles
    
    Returns:
    - A : Tableau NumPy des pourcentages des éléments dans chaque matière première (transposé)
    - C : Tableau NumPy contenant les prix des matières premières
    """
    # Construction de A : le tableau des pourcentages des éléments dans chaque matière première
    # df_A = table_mp.drop(columns=['Article','Code Article'])
    df_A = pd.merge(table_mp, df_mp_dispo[['Article', 'Code Article']], on=['Article', 'Code Article'])
    df_A = df_A.drop(columns=['Article','Code Article'])
    A = df_A.to_numpy().T

    # Récupération des prix des matières premières
    df_C = df_mp_dispo['Prix']
    C = df_C.to_numpy()

    return A, C

def format_constraints_qualite(df_contraints, A,constraints):
    I = list(Impurete_Values.values())
    O = list(ONO_Values.values())
    
    I_min, I_visee, I_max = pd.to_numeric(df_contraints.loc[0:2, 'Impurété'], errors='coerce')
    O_min, O_visee, O_max = pd.to_numeric(df_contraints.loc[0:2, 'ONO'], errors='coerce')

    I, O = map(np.array, (I, O))
    I_dot_A, O_dot_A = I@A, O@A
    # Ajouter les contraintes d'impureté à A_eq et b_eq si nécessaire
    if pd.notna(I_visee):
        constraints['A_eq']['Impurete_visee'] = I_dot_A
        constraints['b_eq']['Impurete_visee'] = I_visee

    # Ajouter les contraintes d'ONO à A_eq et b_eq si nécessaire
    if pd.notna(O_visee):
        constraints['A_eq']['ONO_visee'] = O_dot_A
        constraints['b_eq']['ONO_visee'] = O_visee

    # Ajouter les contraintes d'impureté maximale à A_sup et b_sup si nécessaire
    if pd.notna(I_max):
        constraints['A_sup']['Impurete_max'] = I_dot_A
        constraints['b_sup']['Impurete_max'] = I_max

    # Ajouter les contraintes d'impureté minimale à A_sup et b_sup si nécessaire
    if pd.notna(I_min):
        constraints['A_sup']['Impurete_min'] = -I_dot_A
        constraints['b_sup']['Impurete_min'] = -I_min

    # Ajouter les contraintes d'ONO maximale à A_sup et b_sup si nécessaire
    if pd.notna(O_max):
        constraints['A_sup']['ONO_max'] = O_dot_A
        constraints['b_sup']['ONO_max'] = O_max

    # Ajouter les contraintes d'ONO minimale à A_sup et b_sup si nécessaire
    if pd.notna(O_min):
        constraints['A_sup']['ONO_min'] = -O_dot_A
        constraints['b_sup']['ONO_min'] = -O_min

    return constraints

def format_constraints_MP(df_MP_dispo, constraints):
    bounds = []
    m = df_MP_dispo.shape[0] # m le nb de MP disponibles

    # Contraintes sur les pourcentages sum(x_i) = 1
    constraints['A_eq']["Proportion_Total"] = np.ones(m)
    constraints['b_eq']["Proportion_Total"] = 1

    # Parcours des lignes du DataFrame
    for index, row in df_MP_dispo.iterrows():
        # Récupération des valeurs de "Part Min" et "Part Max", avec une valeur par défaut de 0 et 1 respectivement si elles sont manquantes
        part_min = row['Part Min'] if not pd.isna(row['Part Min']) else 0
        part_max = row['Part Max'] if not pd.isna(row['Part Max']) else 1
        # Ajout du tuple (Part Min, Part Max) à la liste bounds
        bounds.append((part_min, part_max))

        # Les % de MP à consommer
        if not pd.isna(row['Part à consommer']):
            # Construction de A_eq_MP et b_eq_MP
            A_eq = np.zeros(m)
            A_eq[index] = 1
            composant = row['Article']
            constraints['A_eq'][composant] = A_eq
            constraints['b_eq'][composant] = row['Part à consommer']

    return constraints, bounds

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

def format_constraints_elements(df_contraints_element, A,constraints):
    df_contraints_element = Transpose_dataframe(df_contraints_element)
    # Parcours des données de contraintes
    n = A.shape[0]
    for index, row in df_contraints_element.iterrows():
        if not pd.isna(row['Valeur visée']):
            composant = row['Composant'] + '_visee'
            E = np.zeros(n)
            E[index] = 1
            E_dot_A  = E@A
            # print(A.shape,E.shape,E_dot_A.shape)
            constraints['A_eq'][composant] = E_dot_A 
            constraints['b_eq'][composant] = pd.to_numeric(row['Valeur visée'], errors='coerce')

        if not pd.isna(row['Valeur Max par four']):
            composant = row['Composant'] + '_max'
            constraints['A_sup'][composant] = A[index]
            constraints['b_sup'][composant] = pd.to_numeric(row['Valeur Max par four'], errors='coerce')

        if not pd.isna(row['Valeur Min par four']):
            composant = row['Composant'] + '_min'
            constraints['A_sup'][composant] = -A[index]
            constraints['b_sup'][composant] = -pd.to_numeric(row['Valeur Min par four'], errors='coerce')

    return constraints
