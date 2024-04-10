import sys
sys.path.append(r'.\src')


from functions.excel import lire_fichiers_excel, write_dataframe_to_excel
from functions.array_operations import nettoyer_dataframe
from functions.data_processing import construire_tableau, Transpose_dataframe
from functions.constraints import format_constraints_elements, format_constraints_qualite, format_constraints_MP
from functions.linear_programming import solve_linear_program
from functions.result_processing import construct_result_dataframe

def create_optimal_recipe(chemin_fichier_excel):
    # Lire les fichiers Excel
    df_table, df_contraints_element, df_contraints_qualite, df_MP_dispo, df_MP_indispo = lire_fichiers_excel(chemin_fichier_excel)

    # Suppression des matières premières indisponibles
    df_table = nettoyer_dataframe(df_table, df_MP_indispo)

    # Construction de la matrice A et du vecteur C
    A, C = construire_tableau(df_table, df_MP_dispo)

    # Initialisation des listes pour les contraintes
    A_ub, b_ub, A_eq, b_eq = [], [], [], []

    # Mettre  les contraintes concernant les éléments
    df_contraints_element = Transpose_dataframe(df_contraints_element)
    A_ub, b_ub, A_eq, b_eq = format_constraints_elements(A_ub, b_ub, A_eq, b_eq, df_contraints_element, A)

    # Mettre  les contraintes concernant la qualité
    A_ub, b_ub, A_eq, b_eq = format_constraints_qualite(A_ub, b_ub, A_eq, b_eq, df_contraints_qualite, A)

    # Mettre les contraintes concernant les matières premières disponibles
    A_eq, b_eq, bounds = format_constraints_MP(A_eq, b_eq, df_MP_dispo)

    # Résoudre le problème d'optimisation linéaire
    res = solve_linear_program(C, A_ub, b_ub, A_eq, b_eq, bounds)

    # Construire le DataFrame résultant
    df_res = construct_result_dataframe(df_MP_dispo, df_table, res, nb_MP=10)

    # Écrire le DataFrame résultant dans le fichier Excel
    write_dataframe_to_excel(df_res, chemin_fichier_excel, new_sheet_name='Recette')

# Appel de la fonction main avec le chemin du fichier Excel comme argument
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py chemin_fichier_excel")
        sys.exit(1)
    chemin_fichier_excel = sys.argv[1]
    create_optimal_recipe(chemin_fichier_excel)
