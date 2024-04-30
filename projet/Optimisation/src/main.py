import sys
from os.path import abspath
import os


from functions import write_dataframe_to_excel
from functions import read_and_check_input, Separate_data, nettoyer_dataframe
from functions import construire_tableau, Transpose_dataframe
from functions import format_constraints_elements, format_constraints_qualite, format_constraints_MP
from functions import solve_linear_program
from functions import construct_result_dataframe,Save_errors

def create_optimal_recipe(chemin_fichier):
    # Lire les fichiers Excel
    df_table, df_MP, df_contraints, erreurs = read_and_check_input(chemin_fichier)
    if len(erreurs) != 0 :
        return 0
    df_contraints_element, df_contraints_qualite, df_MP_dispo, df_MP_indispo = Separate_data(df_table, df_MP, df_contraints)

    # Suppression des matières premières indisponibles
    df_table = nettoyer_dataframe(df_table, df_MP_indispo)

    # Construction de la matrice A et du vecteur C
    A, C = construire_tableau(df_table, df_MP_dispo)

    # Initialisation des listes pour les contraintes
    A_ub, b_ub, A_eq, b_eq = [], [], [], []

    df_contraints_element = Transpose_dataframe(df_contraints_element)
    # Mettre  les contraintes concernant les éléments
    A_ub, b_ub, A_eq, b_eq = format_constraints_elements(A_ub, b_ub, A_eq, b_eq, df_contraints_element, A)

    # Mettre  les contraintes concernant la qualité
    A_ub, b_ub, A_eq, b_eq = format_constraints_qualite(A_ub, b_ub, A_eq, b_eq, df_contraints_qualite, A)

    # Mettre les contraintes concernant les matières premières disponibles
    A_eq, b_eq, bounds = format_constraints_MP(A_eq, b_eq, df_MP_dispo)


    # Résoudre le problème d'optimisation linéaire
    method = 'simplex' #'interior-point' 'simplex'
    res, ce_result, ci_result = solve_linear_program(C, A_ub, b_ub, A_eq, b_eq,bounds,method)
    conforme = all(val == 1 for val in ce_result) and  all(val == 1 for val in ci_result)    
    # print(method, '\n')
    # print(ce_result, ci_result)
    # print(ce_residuals, ci_residuals)

    erreurs = []
    if not ce_result[0] :
        message = "Erreur : La proportion total n'est pas égale à 1"
        erreurs.append(message)

    # On recupere le chemin du dossier data
    dossier_data = os.path.dirname(chemin_fichier)
    if conforme :
        # Construire le DataFrame résultats
        df_res = construct_result_dataframe(df_MP_dispo, df_table, res)
        # Écrire le DataFrame résultats dans le fichier Excel
        write_dataframe_to_excel(df_res, dossier_data, new_sheet_name='Recette')
        print("Le problème admet une solution optimale.")
    else : 
        df_res = construct_result_dataframe(df_MP_dispo, df_table, res)
        # Sauvegarder les erreurs dans un fichier texte
        message = "Veillez revoir les contraintes de la feuille 'Contraintes Qualités et Elément' et/ou 'Contraintes matières premières'"
        erreurs.append(message)
        Save_errors(erreurs, dossier_data, res, A, df_contraints_qualite, df_contraints_element,df_MP_dispo )
        print("Les erreurs ont été enregistrées dans le fichier erreurs.txt")
    return 

# Appel de la fonction main avec le chemin du fichier Excel comme argument
if __name__ == "__main__":
    # Vérifiez si un chemin de fichier Excel est fourni en argument
    if len(sys.argv) != 2:
        print("Usage: python main.py chemin_vers_fichier_excel")
        sys.exit(1)

    # Récupérez le chemin du fichier Excel à partir des arguments de ligne de commande
    chemin_fichier_excel = abspath(sys.argv[1])

    # Appelez la fonction create_optimal_recipe avec le chemin du fichier Excel
    create_optimal_recipe(chemin_fichier_excel)