import pandas as pd
import numpy as np
import os
from .constants import Impurete_Values, ONO_Values

def construct_result_dataframe(df_MP_dispo, df_table, res):
    # Création d'un nouveau DataFrame avec les colonnes 'Article','Métallique ?' et 'Prix' de df_MP_dispo
    df_res = pd.DataFrame(df_MP_dispo[['Article', 'Prix','Métallique ?']])
    
    # Ajout de la colonne 'Proportion' avec les valeurs de res.x
    df_res['Proportion'] = res.x
    
    # Calcul de la colonne 'Valeur (/T)' en multipliant 'Proportion' par 'Prix'
    df_res['Valeur (/T)'] = df_res['Proportion'] * df_res['Prix']
    
    # Garder les Proportions non nulles seulement
    df_res = df_res[(df_res['Proportion'] > 0)]


    # Trier le DataFrame par 'Proportion' de manière décroissante
    df_res = df_res.sort_values(by='Proportion', ascending=False)
    
    # Initialiser les colonnes 'ONO' et 'Impurete' avec des valeurs NaN
    df_res['ONO'] = np.nan
    df_res['Impurete'] = np.nan
    
    # Définir les seuils pour chaque valeur de la colonne 'Métallique ?'
    seuil_0 = 0.0001
    seuil_1 = 0.01 #0.01

    # Filtrer les lignes en fonction de la valeur de la colonne 'Métallique ?' et du seuil correspondant
    df_res = df_res[(df_res['Métallique ?'] == 0) & (df_res['Proportion'] >= seuil_0) |
                    (df_res['Métallique ?'] == 1) & (df_res['Proportion'] >= seuil_1)]


    df_res = df_res.drop(columns=['Métallique ?'])
    Article_selected = df_res.loc[:, 'Article'].tolist()
    
    # Récupérer les éléments chimiques correspondant aux articles sélectionnés
    Element_selected = df_table[df_table['Article'].isin(Article_selected)]
    df_res = pd.merge(df_res, Element_selected, on='Article', how='inner')
    
    # Effectuer un saut de ligne dans df_res
    n_ligne = len(df_res)
    df_res.loc[n_ligne] = np.nan
    n_ligne += 1
    
    # Ajout de la partie résultats
    df_res.loc[n_ligne, 'Article'] = 'Resultats'
    
    # Ajouter la somme des colonnes 'Proportion' et 'Valeur (/T)' dans la ligne des résultats
    df_res.loc[n_ligne, ['Proportion', 'Valeur (/T)']] = [df_res['Proportion'].sum(), df_res['Valeur (/T)'].sum()]

    
    # Calcul des proportions des éléments dans la fonte
    cols_to_multiply = df_res.columns[df_res.columns.get_loc('C'):]
    proportion_elements = []
    for col in cols_to_multiply:
        part_element = (df_res['Proportion'] * df_res[col]).sum()
        proportion_elements.append(part_element)
    
    # Ajout des valeurs des proportions des éléments
    df_res.loc[n_ligne, 'C':] = proportion_elements
    
    # Ajout des valeurs des indicateurs qualité
    I,O  = map(np.array,(Impurete_Values, ONO_Values))
    proportion_elements = np.array(proportion_elements)
    df_res.loc[n_ligne, 'Impurete'] = I @ proportion_elements
    df_res.loc[n_ligne, 'ONO'] = O @ proportion_elements
    
    return df_res

def Save_errors(message, dossier_data):
    # Supprimer le fichier existant des résultats s'il existe
    fichier_Resultats = os.path.join(dossier_data, 'Resultats.xlsx')
    if os.path.exists(fichier_Resultats):
        os.remove(fichier_Resultats)
    
    # Sauvegarder les erreurs dans un fichier texte
    erreurs = []
    erreurs.append(message)
    fichier_erreurs = os.path.join(dossier_data, 'erreurs.txt')
    with open(fichier_erreurs, "w", encoding="utf-8") as f:
        for erreur in erreurs:
            f.write(erreur + "\n")

def construct_result_dataframe2(df_MP_dispo, df_table, res):
    # Création d'un nouveau DataFrame avec les colonnes 'Article','Métallique ?' et 'Prix' de df_MP_dispo
    df_res = pd.DataFrame(df_MP_dispo[['Article', 'Prix','Métallique ?']])
    
    # Ajout de la colonne 'Proportion' avec les valeurs de res.x
    df_res['Proportion'] = res.x
    
    # Calcul de la colonne 'Valeur (/T)' en multipliant 'Proportion' par 'Prix'
    df_res['Valeur (/T)'] = df_res['Proportion'] * df_res['Prix']
    
    # Arrondir les colonnes 'Proportion' et 'Valeur (/T)' à 3 décimales
    # df_res.loc[:, ['Proportion', 'Valeur (/T)']] = df_res[['Proportion', 'Valeur (/T)']].round(3)
    df_res.loc[:, ['Proportion', 'Valeur (/T)']] = df_res[['Proportion', 'Valeur (/T)']]
    
    # Trier le DataFrame par 'Proportion' de manière décroissante
    df_res = df_res.sort_values(by='Proportion', ascending=False)
    
    # Initialiser les colonnes 'ONO' et 'Impurete' avec des valeurs NaN
    df_res['ONO'] = np.nan
    df_res['Impurete'] = np.nan
    
    # # Définir les seuils pour chaque valeur de la colonne 'Métallique ?'
    # seuil_0 = 0.001
    # seuil_1 = 0.001 #0.01

    # # Filtrer les lignes en fonction de la valeur de la colonne 'Métallique ?' et du seuil correspondant
    # df_res = df_res[(df_res['Métallique ?'] == 0) & (df_res['Proportion'] >= seuil_0) |
    #                 (df_res['Métallique ?'] == 1) & (df_res['Proportion'] >= seuil_1)]


    df_res = df_res.drop(columns=['Métallique ?'])
    Article_selected = df_res.loc[:, 'Article'].tolist()
    
    # Récupérer les éléments chimiques correspondant aux articles sélectionnés
    Element_selected = df_table[df_table['Article'].isin(Article_selected)]
    df_res = pd.merge(df_res, Element_selected, on='Article', how='inner')
    
    # Effectuer un saut de ligne dans df_res
    n_ligne = len(df_res)
    df_res.loc[n_ligne] = np.nan
    n_ligne += 1
    
    # Ajout de la partie résultats
    df_res.loc[n_ligne, 'Article'] = 'Resultats'
    
    # Ajouter la somme des colonnes 'Proportion' et 'Valeur (/T)' dans la ligne des résultats
    df_res.loc[n_ligne, ['Proportion', 'Valeur (/T)']] = [df_res['Proportion'].sum(), df_res['Valeur (/T)'].sum()]

    
    # Calcul des proportions des éléments dans la fonte
    cols_to_multiply = df_res.columns[df_res.columns.get_loc('C'):]
    proportion_elements = []
    for col in cols_to_multiply:
        part_element = (df_res['Proportion'] * df_res[col]).sum()
        proportion_elements.append(part_element)
    
    # Ajout des valeurs des proportions des éléments
    df_res.loc[n_ligne, 'C':] = proportion_elements
    
    # Ajout des valeurs des indicateurs qualité
    I = np.array([0, 0, 0.44, 4.90, 0.37, 5.60, 0.37, 7.90, 39.00, 0, 0, 0, 0, 0, 4.40, 0, 0, 0])
    O = np.array([0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1])
    proportion_elements = np.array(proportion_elements)
    df_res.loc[n_ligne, 'Impurete'] = I @ proportion_elements
    df_res.loc[n_ligne, 'ONO'] = O @ proportion_elements
    
    return df_res