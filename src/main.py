import sys
from os.path import abspath

from functions import lire_fichiers_excel, write_dataframe_to_excel
from functions import nettoyer_dataframe
from functions import construire_tableau, Transpose_dataframe
from functions import format_constraints_elements, format_constraints_qualite, format_constraints_MP
from functions import solve_linear_program
from functions import construct_result_dataframe


def create_optimal_recipe(chemin_fichier_excel):
    # Lire les fichiers Excel
    df_table, df_contraints_element, df_contraints_qualite, df_MP_dispo, df_MP_indispo = lire_fichiers_excel(chemin_fichier_excel)

    # Suppression des matières premières indisponibles
    df_table = nettoyer_dataframe(df_table, df_MP_indispo)

    # Construction de la matrice A et du vecteur C
    A, C = construire_tableau(df_table, df_MP_dispo)

    # Initialisation des listes pour les contraintes
    A_ub, b_ub, A_eq, b_eq = [], [], [], []

    # Mettre les contraintes concernant les matières premières disponibles
    A_eq, b_eq, bounds = format_constraints_MP(A_eq, b_eq, df_MP_dispo)

    # Mettre  les contraintes concernant la qualité
    A_ub, b_ub, A_eq, b_eq = format_constraints_qualite(A_ub, b_ub, A_eq, b_eq, df_contraints_qualite, A)


    # Mettre  les contraintes concernant les éléments
    df_contraints_element = Transpose_dataframe(df_contraints_element)
    A_ub, b_ub, A_eq, b_eq = format_constraints_elements(A_ub, b_ub, A_eq, b_eq, df_contraints_element, A)

    # Résoudre le problème d'optimisation linéaire
    res = solve_linear_program(C, A_ub, b_ub, A_eq, b_eq, bounds)


    if res.x.any() != None:
        # Construire le DataFrame résultant
        df_res = construct_result_dataframe(df_MP_dispo, df_table, res)
        # Écrire le DataFrame résultant dans le fichier Excel
        write_dataframe_to_excel(df_res, chemin_fichier_excel, new_sheet_name='Recette')
    else :
        print("Le problème n'admet pas de solution.")

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