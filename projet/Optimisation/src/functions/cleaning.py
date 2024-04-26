import pandas as pd
import os



def supprimer_fichier(chemin_fichier, file_name = 'Resultats.xlsx'):
    # Créer le chemin complet du nouveau fichier Excel pour les résultats
    dossier_data = os.path.dirname(chemin_fichier)
    fichier_Resultats = os.path.join(dossier_data,file_name)

    # Vérifier si le fichier Excel existe déjà
    if os.path.exists(fichier_Resultats):
        # Supprimer le fichier existant
        os.remove(fichier_Resultats)


def read_and_check_input(chemin_fichier): 
    # Lecture de la première feuille du fichier Excel : Table Matière Element
    df_table = pd.read_excel(chemin_fichier, engine='calamine')
    # Lecture de la deuxième feuille du fichier Excel : Contraintes Element
    df_contraints = pd.read_excel(chemin_fichier, engine='calamine', sheet_name=1)
    # Lecture de la troisième feuille du fichier Excel : Contraintes Matière Première
    df_MP = pd.read_excel(chemin_fichier, engine='calamine', sheet_name=2)
    df_MP = df_MP.rename(columns=df_MP.iloc[0]).drop(df_MP.index[0])

    # Création d'une liste pour stocker les erreurs
    erreurs =  []
    # Contraintes MP
    # Colonne 'Métallique ?' et 'Disponible ?'
    valid_values = (df_MP['Disponible ?'].isin([0, 1])) & (df_MP['Métallique ?'].isin([0, 1]))
    if  not valid_values.all():
        message = "Erreur : Les valeurs possibles de 'Disponible ?' et de 'Métallique ?' sont 0 ou 1."
        erreurs.append(message)

    # Colonne 'Prix'
    valid_values =(df_MP['Prix'].apply(lambda x: isinstance(x, (int, float)))) & (not df_MP['Prix'].isna().any())
    if  not valid_values.all():
        message = "Erreur : 'Prix' doit prendre des nombres décimaux"
        erreurs.append(message)

    valid_values = df_MP[~(((df_MP['Part Min'] <= df_MP['Part à consommer']) & 
                          (df_MP['Part à consommer'] <= df_MP['Part Max'])) | 
                         (df_MP['Part à consommer'].isna()))]
    if valid_values.shape[0] != 0:
        erreurs.append("Erreur : Les valeurs de 'Part à consommer' sont en dehors des limites spécifiées ")

    valid_values = df_MP[~((df_MP['Part Max'] >= df_MP['Part Min']) | 
                         (df_MP['Part Max'].isna()) | 
                         (df_MP['Part Min'].isna()))]
    if valid_values.shape[0] != 0:
        erreurs.append("Erreur : Les valeurs de 'Part Max' doivent être inférieures à 'Part Min'")

    # Tableau des MP et des elements chimiques
    valid_values = df_table [df_table.columns[1:]].apply(lambda x: (x >= 0) & (x <= 100)).all(axis=1)
    if not valid_values.all():
        erreurs.append("Erreur : Certaines valeurs de Tableau A sont en dehors de la plage autorisée (0-100).")


    # # Contraintes qualité et élement
    # valid_values = df_contraints[df_contraints.columns[1:]].apply(lambda x: (x >= 0) & (x <= 100)).all(axis=1)
    # if not valid_values.all():
    #     erreurs.append("Erreur : Certaines valeurs des Contraintes qualité et élement sont en dehors de la plage autorisée (0-100).")

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
    return df_table, df_MP, df_contraints, erreurs


def Separate_data(df_table, df_MP, df_contraints): 
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
