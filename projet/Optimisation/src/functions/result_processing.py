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
    
    # # Définir les seuils pour chaque valeur de la colonne 'Métallique ?'
    # seuil_0 = 0.0001
    # seuil_1 = 0.01 #0.01

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
    I,O  = map(np.array,(list(Impurete_Values.values()), list(ONO_Values.values())))
    proportion_elements = np.array(proportion_elements)
    df_res.loc[n_ligne, 'Impurete'] = I @ proportion_elements
    df_res.loc[n_ligne, 'ONO'] = O @ proportion_elements
    
    return df_res

def Save_errors(erreurs, dossier_data, res, A, df_contraints_qualite, df_contraints_element, df_MP_dispo ):
    # Supprimer le fichier existant des résultats s'il existe
    fichier_Resultats = os.path.join(dossier_data, 'Resultats.xlsx')
    if os.path.exists(fichier_Resultats):
        os.remove(fichier_Resultats)
    
    # Sauvegarder les erreurs dans un fichier texte
    I,O  = map(np.array,(list(Impurete_Values.values()), list(ONO_Values.values())))
    n_ligne = df_contraints_qualite.shape[0]
    df_contraints_qualite.loc[n_ligne,'Composant'] = 'Valeur obtenu'
    df_contraints_qualite.loc[n_ligne,'Impurété'] = I @ (np.dot(A,res.x))
    df_contraints_qualite.loc[n_ligne,'ONO'] = O @ (np.dot(A,res.x))
    df_qualite_result = df_contraints_qualite.iloc[-1:]
    df_contraints_element['Valeur obtenu'] = np.dot(A,res.x)
    df_element_result = df_contraints_element[['Composant', 'Valeur obtenu']]
    df_MP_result = df_MP_dispo[['Article', 'Part à consommer']]
    df_MP_result.loc[:, ['Proportion']] = res.x
    df_MP_result = df_MP_result.dropna()


    df_result = pd.DataFrame(df_MP_dispo[['Article']])
    # Ajout de la colonne 'Proportion' avec les valeurs de res.x
    df_result['Proportion'] = res.x
    df_result = df_result[(df_result['Proportion'] > 0)]
    df_result = df_result.sort_values(by='Proportion', ascending=False)


    # Ajout de la partie résultats
    n_ligne = df_result.shape[0]
    df_result.loc[n_ligne,'Article'] = 'Somme Total'
    
    # Ajouter la somme des colonnes 'Proportion' et 'Valeur (/T)' dans la ligne des résultats
    df_result.loc[n_ligne,['Proportion']] = df_result['Proportion'].sum()



    fichier_erreurs = os.path.join(dossier_data, 'erreurs.txt')
    with open(fichier_erreurs, "w", encoding="utf-8") as f:
        for erreur in erreurs:
            f.write(erreur + "\n")
        f.write("\n")
        f.write("Voici une proposition :"+ "\n" + "\n")

    # Écrire le DataFrame dans le fichier
    df_result.to_csv(fichier_erreurs, sep='\t', index=False,  mode='a',  header=True)
    with open(fichier_erreurs, "a", encoding="utf-8") as f:
        f.write("\n")
    df_qualite_result.to_csv(fichier_erreurs, sep='\t', index=False,  mode='a')
    # Ajouter un espace entre les deux écritures
    with open(fichier_erreurs, "a", encoding="utf-8") as f:
        f.write("\n")
    df_element_result.to_csv(fichier_erreurs, sep='\t', index=False, mode='a', header=False)
    # Ajouter un espace entre les deux écritures
    with open(fichier_erreurs, "a", encoding="utf-8") as f:
        f.write("\n")
    df_MP_result.to_csv(fichier_erreurs, sep='\t', index=False, mode='a', header=True)
    
    return 

