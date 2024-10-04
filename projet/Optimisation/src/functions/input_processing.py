import os
import pandas as pd



def Give_contraints_per_recipe(Contraintes_Elements ) :

    # Supprimer les lignes entièrement vides de Contraintes_Elements
    Contraintes_Elements = Contraintes_Elements.dropna(how='all').reset_index(drop=True)

    # Obtenir les valeurs de la première colonne sous forme de liste
    liste_des_recettes = Contraintes_Elements[Contraintes_Elements.columns[0]].tolist()

    # Insérer le nom de la colonne au début de la liste
    liste_des_recettes.insert(0, Contraintes_Elements.columns[0])

    # Obtenir les types de recettes uniques
    types_de_recettes = Contraintes_Elements[Contraintes_Elements.columns[0]].dropna().unique().tolist()

    # Ajouter le nom de la colonne à la liste des types de recettes
    types_de_recettes.append(Contraintes_Elements.columns[0])

    # Initialiser un dictionnaire pour les contraintes par recettes
    contraintes_par_recettes = {}

    # Parcourir la liste des recettes
    for idx, recette in enumerate(liste_des_recettes):
        # Vérifier si la recette est un type de recette
        if recette in types_de_recettes:
            # Ajouter les contraintes de la recette au dictionnaire
            contraintes_par_recettes[recette] = Contraintes_Elements.iloc[idx:idx+3, 1:].reset_index(drop=True)

    return contraintes_par_recettes

def Give_contraints_MP_per_recipe(Matieres_premiere):
    # Liste des noms de colonnes non par défaut
    types_de_recettes = [col for col in Matieres_premiere.columns if not col.startswith('Unnamed')]

    # Initialisation du dictionnaire des contraintes par recette
    contraintes_mp = {}

    # Création des DataFrames en fonction des colonnes non par défaut
    for recette in types_de_recettes:
        # Récupération de l'index de la colonne de la recette
        idx = Matieres_premiere.columns.get_loc(recette)
        
        # Sélection des colonnes pertinentes pour la recette
        cols = ['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 2', recette] + [f'Unnamed: {i}' for i in range(idx + 1, idx + 5)]
        
        # Création du DataFrame pour la recette
        df_recette = Matieres_premiere[cols]
        
        # Suppression des premières lignes inutiles
        df_recette = df_recette.iloc[1:].reset_index(drop=True)
        
        # Renommage des colonnes avec les valeurs de la première ligne
        df_recette = df_recette.rename(columns=df_recette.iloc[0]).drop(df_recette.index[0]).reset_index(drop=True)
        
        # Ajout du DataFrame au dictionnaire des contraintes
        contraintes_mp[recette] = df_recette

    return contraintes_mp

def check_MP_and_contraints_values(df_mp,df_elmt_and_quality,erreurs): 
    # Contraintes MP
    # Colonne 'Métallique ?' et 'Disponible ?'
    valid_values = (df_mp['Disponible ?'].isin([0, 1])) & (df_mp['Métallique ?'].isin([0, 1]))
    if  not valid_values.all():
        message = "Erreur : Les valeurs possibles de 'Disponible ?' et de 'Métallique ?' sont 0 ou 1."
        erreurs.append(message)

    # Colonne 'Prix'
    valid_values =(df_mp['Prix'].apply(lambda x: isinstance(x, (int, float)))) & (not df_mp['Prix'].isna().any())
    if  not valid_values.all():
        message = "Erreur : 'Prix' doit prendre des nombres décimaux"
        erreurs.append(message)

    valid_values = df_mp[~(((df_mp['Part Min'] <= df_mp['Part à consommer']) & 
                          (df_mp['Part à consommer'] <= df_mp['Part Max'])) | 
                         (df_mp['Part à consommer'].isna()))]
    if valid_values.shape[0] != 0:
        erreurs.append("Erreur : Les valeurs de 'Part à consommer' sont en dehors des limites spécifiées ")

    valid_values = df_mp[~((df_mp['Part Max'] >= df_mp['Part Min']) | 
                         (df_mp['Part Max'].isna()) | 
                         (df_mp['Part Min'].isna()))]
    if valid_values.shape[0] != 0:
        erreurs.append("Erreur : Les valeurs de 'Part Max' doivent être inférieures à 'Part Min'")


    # Contraintes qualité et élement
    # Convertir toutes les valeurs en numériques, les chaînes non convertibles deviendront NaN
    df_numeric = df_elmt_and_quality[df_elmt_and_quality.columns[1:]].apply(pd.to_numeric, errors='coerce')

    # Vérifier les valeurs dans la plage 0-100 ou NaN
    valid_values = df_numeric.apply(lambda x: ((x >= 0) & (x <= 100)) | x.isna()).all(axis=1)

    if not valid_values.all():
        erreurs.append("Erreur : Certaines valeurs des Contraintes qualité et élement sont en dehors de la plage autorisée (0-100).")

    return 

def check_table_values(df_table,erreurs): 
    # Tableau des MP et des elements chimiques
    valid_values = df_table [df_table.columns[2:]].apply(lambda x: (x >= 0) & (x <= 100)).all(axis=1)
    if not valid_values.all():
        erreurs.append("Erreur : Certaines valeurs de Tableau A sont en dehors de la plage autorisée (0-100).")
    return


#----------------------------- Version Cle USB ----------------------------- 

def read_and_check_USB_input_values(chemin_fichier): 

    # Lecture de la première feuille du fichier Excel : Table Matière Element
    Tableau_Matiere_Element = pd.read_excel(chemin_fichier, engine='openpyxl') # 'calamine'

    # Lecture de la deuxième feuille du fichier Excel : Contraintes Element
    Contraintes_Elements = pd.read_excel(chemin_fichier, engine='openpyxl', sheet_name=1) # 'calamine'
    # Lecture de la troisième feuille du fichier Excel : Contraintes Matière Première
    Matieres_premiere = pd.read_excel(chemin_fichier, engine='openpyxl', sheet_name=2) # 'calamine'

    # Separation des contraintes par types de recettes
    contraintes_mp = Give_contraints_MP_per_recipe(Matieres_premiere)
    contraintes_elmt_and_quality = Give_contraints_per_recipe(Contraintes_Elements)

    erreurs =[]
    check_table_values(Tableau_Matiere_Element,erreurs) 

    for recette in contraintes_elmt_and_quality :
        df_elmt_and_quality = contraintes_elmt_and_quality[recette]
        df_mp = contraintes_mp[recette]
        check_MP_and_contraints_values(df_mp,df_elmt_and_quality,erreurs)
    
    if erreurs:
        # Créer le chemin complet du nouveau fichier Excel
        dossier_data = os.path.dirname(chemin_fichier)
        fichier_erreurs = os.path.join(dossier_data, 'erreurs.txt')

        with open(fichier_erreurs, "w", encoding="utf-8") as f:
            for erreur in erreurs:
                f.write(erreur + "\n")
        print("Les erreurs ont été enregistrées dans le fichier '{}'.".format(fichier_erreurs))


        # Créer le chemin complet du nouveau fichier Excel
        dossier_data = os.path.dirname(chemin_fichier)
        fichier_Resultats = os.path.join(dossier_data, 'Resultats.xlsx')

        # Vérifier si le fichier Excel existe déjà
        if os.path.exists(fichier_Resultats):
            # Supprimer le fichier existant
            os.remove(fichier_Resultats)
    return Tableau_Matiere_Element, contraintes_mp, contraintes_elmt_and_quality, erreurs


#----------------------------- Version FDN ----------------------------- 


def read_and_check_FDN_input_values(chemin_dossier, recetteName): 

    chemin_fichier_1 = os.path.join(chemin_dossier, 'recipe_optimization_data_1.csv')
    chemin_fichier_2 = os.path.join(chemin_dossier, 'recipe_optimization_data_2.csv')
    chemin_fichier_3 = os.path.join(chemin_dossier, 'recipe_optimization_data_3.csv')

    # Lecture de la première feuille du fichier CSV : Table Matière Element
    Tableau_Matiere_Element = pd.read_csv(chemin_fichier_1, sep=';', encoding='UTF-8')
    # Lecture de la deuxième feuille du fichier CSV : Contraintes Element
    Contraintes_Elements = pd.read_csv(chemin_fichier_2, sep=';', encoding='UTF-8') # 'ISO-8859-1'
    # Lecture de la troisième feuille du fichier CSV : Contraintes Matière Première
    Matieres_premiere = pd.read_csv(chemin_fichier_3, sep=';', encoding='UTF-8')

    # Pour utiliser create_optimal_recipe on a besoin l'écrire avec des dictionnaires
    contraintes_mp, elmt_quality_constraints = {}, {}
    contraintes_mp[recetteName] = Matieres_premiere
    elmt_quality_constraints[recetteName] = Contraintes_Elements

    erreurs =[]
    check_table_values(Tableau_Matiere_Element,erreurs) 
    check_MP_and_contraints_values(Matieres_premiere,Contraintes_Elements,erreurs)
    if erreurs:
        # Créer le chemin complet du nouveau fichier Excel
        fichier_erreurs = os.path.join(chemin_dossier, 'erreurs.txt')

        with open(fichier_erreurs, "w", encoding="utf-8") as f:
            for erreur in erreurs:
                f.write(erreur + "\n")
        print("Les erreurs ont été enregistrées dans le fichier '{}'.".format(fichier_erreurs))


        # Créer le chemin complet du nouveau fichier Excel
        fichier_Resultats = os.path.join(chemin_dossier, 'resultats.xlsx')

        # Vérifier si le fichier Excel existe déjà
        if os.path.exists(fichier_Resultats):
            # Supprimer le fichier existant
            os.remove(fichier_Resultats)

        # Créer le chemin complet du nouveau fichier Excel
        fichier_ResultatsComposition = os.path.join(chemin_dossier, 'resultatsComposition.xlsx')

        # Vérifier si le fichier Excel existe déjà
        if os.path.exists(fichier_ResultatsComposition):
            # Supprimer le fichier existant
            os.remove(fichier_ResultatsComposition)

    return Tableau_Matiere_Element, contraintes_mp, elmt_quality_constraints, erreurs

