import os
import pandas as pd
import plotly.express as px



def fusion_and_clean_excel_files(files_list):
    """
    Cette fonction prend une liste de chemins de fichiers Excel et une liste de noms de colonnes à supprimer,
    lit les fichiers, effectue un nettoyage et des transformations sur les données, puis retourne un DataFrame final.

    Args:
    files_list (list): Liste des chemins des fichiers Excel à traiter.

    Returns:
    DataFrame: Le DataFrame final après le traitement.
    """
    # Lire les fichiers Excel et les concaténer
    dfs = []
    for file in files_list:
        df = pd.read_excel(file, engine='calamine')
        dfs.append(df)
    df = pd.concat(dfs).reset_index(drop=True)


    # Colonnes à supprimer
    columns_to_remove = ['Date','Rp0.2','A%','Contre-essai A%','Pièces','Observations','Comment. RQ','PJ','Ca','Ba']

    # Supprimer les colonnes spécifiées
    df.drop(columns=columns_to_remove, inplace=True)
    
    # Supprimer les lignes avec des valeurs manquantes
    df.dropna(inplace=True)
    
    # Rajouter le critère de pureté de MAYER
    df['Purete MAYER [%]'] = 0
    
    # Renommer les colonnes
    new_names = ['Recette','Numéro de four','Conforme ?', 'Rm [MPA]', 'Moyenne allongement [%]', 'Impureté [%]','Ferrite [%]', 'Purete ONO [%]', 'Purete THIELMANN [%]',
                 'C [%]', 'Si [%]', 'Mn [%]', 'Cu [%]', 'Cr [%]', 'P [%]', 'Ni [%]', 'Mo [%]', 'Sn [%]', 'Sb [%]', 'Al [%]', 'S [%]', 'Mg [%]', 'Pb [%]', 'Ti [%]', 'As [%]', 'Bi [%]', 'V [%]','Purete MAYER [%]']
    df = df.set_axis(new_names, axis='columns')

    
    # Modifier l'ordre des colonnes
    column_order = ['Recette', 'Numéro de four', 'Conforme ?', 'Rm [MPA]', 'Moyenne allongement [%]', 'Impureté [%]', 'Ferrite [%]', 'Purete ONO [%]', 'Purete THIELMANN [%]', 'Purete MAYER [%]',
                    'C [%]', 'Si [%]', 'Mn [%]', 'Cu [%]', 'Cr [%]', 'P [%]', 'Ni [%]', 'Mo [%]', 'Sn [%]', 'Sb [%]', 'Al [%]', 'S [%]', 'Mg [%]', 'Pb [%]', 'Ti [%]', 'As [%]', 'Bi [%]', 'V [%]']
    df = df.reindex(columns = column_order)
    
    # Supprimer les lignes doublons en se basant sur les colonnes spécifiées 
    df = df.drop_duplicates(subset=['Numéro de four','Impureté [%]', 'Ferrite [%]', 'Purete ONO [%]', 'Purete THIELMANN [%]', 'Purete MAYER [%]', 'C [%]', 'Si [%]', 'Mn [%]', 'Cu [%]', 'Cr [%]', 'P [%]', 'Ni [%]', 'Mo [%]', 'Sn [%]', 'Sb [%]', 'Al [%]', 'S [%]', 'Mg [%]', 'Pb [%]', 'Ti [%]', 'As [%]', 'Bi [%]', 'V [%]'])

    return df

def add_quality(df):
    """
    Cette fonction ajoute des colonnes pour les mesures de qualité basées sur des équations spécifiques.

    Args:
    df (DataFrame): Le DataFrame contenant les données.

    Returns:
    DataFrame: Le DataFrame avec les colonnes de qualité ajoutées.
    """
    df['Impureté [%]'] = 4.9 * df['Cu [%]'] + 0.37 * (df['Ni [%]'] + df['Cr [%]']) + 7.9 * df['Mo [%]'] + 4.4 * df['Ti [%]'] + 39.0 * df['Sn [%]'] + 0.44 * df['Mn [%]'] + 5.6 * df['P [%]']
    df['Ferrite [%]'] = 92.3 - 96.2 * df['Mn [%]'] - 211 * df['Cu [%]'] - 14270 * df['Pb [%]'] - 2815 * df['Sb [%]']
    df['Purete ONO [%]'] = df['Cu [%]'] + df['Ti [%]'] + df['Ni [%]'] + df['Cr [%]'] + df['V [%]'] + df['Al [%]'] + df['As [%]'] + df['Sn [%]'] + df['Pb [%]'] + df['Sb [%]'] + df['Bi [%]']
    df['Purete THIELMANN [%]'] = 4.4 * df['Ti [%]'] + 2.0 * df['As [%]'] + 2.3 * df['Sn [%]'] + 5.0 * df['Sb [%]'] + 290 * df['Pb [%]'] + 370 * df['Bi [%]'] + 1.6 * df['Al [%]']
    df['Purete MAYER [%]'] = df['Ti [%]'] + (df['Pb [%]'] + df['Bi [%]']) + df['Sb [%]']
    return df

def keep_GS_and_add_quality(df):
    """ 
    Cette fonction prend un DataFrame contenant des données de recettes et réalise plusieurs étapes de traitement:
    1. Filtrer les recettes pour ne garder que celles de type 'GS *-*'.
    2. Renommer la colonne 'Recette' en suivant le motif 'GS *-*'.
    3. Extraire les valeurs numériques de la colonne 'Recette' et les convertir en entiers pour créer les colonnes 'Ref_Rm' et 'Ref_Al'.
    4. Trier les données en fonction des valeurs numériques de la colonne 'Recette'.
    5. Supprimer les colonnes 'Ref_Rm' et 'Ref_Al'.
    6. Ajouter des équations de qualité avec une fonction 'add_quality' (non définie ici).
    7. Arrondir les valeurs des colonnes à 2 ou 3 décimales selon leur type.
    
    Arguments:
    - df : DataFrame pandas contenant les données de recettes
    
    Retour:
    - df : DataFrame pandas traité avec les étapes décrites ci-dessus
    """
    # On ne garde que les Recettes de type: 'GS *-*'
    df = df[df['Recette'].str.contains(r'^GS', regex=True)]
    
    # Renommer la colonne 'Recette' selon le motif 'GS *-*'
    df_modif = df['Recette'].str.extract(r'(GS \d+-\d+)')
    df.loc[:, 'Recette'] = df_modif.loc[:, 0].to_list()
    
    # Extraire les valeurs numériques de la colonne 'Recette' et les convertir en entiers
    df.loc[:, ['Ref_Rm', 'Ref_Al']] = df['Recette'].str.extract(r'(\d+)-(\d+)').astype(int)

    
    # Trier les données en fonction des valeurs numériques de la colonne 'Recette'
    df = df.sort_values(by=['Ref_Rm', 'Ref_Al'])
    
    # Supprimer les colonnes 'Ref_Rm' et 'Ref_Al'
    df = df.drop(columns=['Ref_Rm', 'Ref_Al'])
    
    # Ajouter des équations de qualité
    df = add_quality(df)
    
    # Arrondir les valeurs des colonnes à 2,3 décimales
    colonnes_2 = ['Moyenne allongement [%]', 'Impureté [%]', 'Ferrite [%]', 'Purete ONO [%]', 'Purete THIELMANN [%]']
    df.loc[:, colonnes_2] = df[colonnes_2].round(2)
    
    colonnes_3 = ['Purete MAYER [%]', 'C [%]', 'Si [%]', 'Mn [%]', 'Cu [%]', 'Cr [%]', 'P [%]', 'Ni [%]', 'Mo [%]', 'Sn [%]', 'Sb [%]', 'Al [%]', 'S [%]', 'Mg [%]', 'Pb [%]', 'Ti [%]', 'As [%]', 'Bi [%]', 'V [%]']
    df.loc[:, colonnes_3] = df[colonnes_3].round(3)
    
    return df

def split_GS(recipe_name, df):
    # Séparation des données par type de recettes
    df_recipe = df[df['Recette'] == recipe_name]
    
    # Séparation conforme/non conforme de chaque type de recettes
    df_conforme = df_recipe[df_recipe['Conforme ?'] == 1]
    df_nonconforme = df_recipe[df_recipe['Conforme ?'] == 0]
    
    # Définir les attributs de tri
    sort_attributes = ['Rm [MPA]', 'Moyenne allongement [%]']
    
    # Trier les données en fonction de Rm et Al de la recette
    df_recipe = df_recipe.sort_values(by=sort_attributes)
    df_nonconforme = df_nonconforme.sort_values(by=sort_attributes)
    df_conforme = df_conforme.sort_values(by=sort_attributes)

    # exportation des données
    output_dir = os.path.join('..', 'data', 'données nettoyées')

    # Vérifier si le dossier existe, sinon le créer
    if not os.path.exists(output_dir ):
        os.makedirs(output_dir )
    # Exportation des données fusionnées
    merged_file_path = os.path.join(output_dir, f"Traction.xlsx")
    df.to_excel(merged_file_path, index=False)

    # Exportation des données non conformes et conformes dans le même fichier
    file_path = os.path.join(output_dir, f"{recipe_name}.xlsx")
    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        df_nonconforme.to_excel(writer, sheet_name='Non Conforme', index=False)
        df_conforme.to_excel(writer, sheet_name='Conforme', index=False)
        
    return df_nonconforme, df_conforme
