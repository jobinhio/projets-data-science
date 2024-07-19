import sys
from os.path import abspath
import os
from tqdm import tqdm
import pandas as pd


from functions import Separate_data, clean_table_mp  
from functions import read_and_check_input_values 
from functions import create_matrix_A_and_C,format_constraints_elements
from functions import format_constraints_qualite, format_constraints_MP
from functions import solve_linear_program
from functions import optimize_with_correction
from functions import  gestion_resultats,construct_result_dataframe,export_result,save_errors,remove_old_recipes
def create_optimal_recipe(recette,table_mp, mp_constraints, elmt_quality_constraints,dossier_data):
    
    # df_mp = mp_constraints[recette]
    # df_elmt_and_quality = elmt_quality_constraints[recette]

    # df = Separate_data(table_mp, df_mp, df_elmt_and_quality)
    # df_contraints_element, df_contraints_qualite = df[0],df[1]
    # df_mp_dispo, df_mp_indispo = df[2],df[3]
    
    df_mp, df_elmt_and_quality = mp_constraints[recette], elmt_quality_constraints[recette]
    df_contraints_element, df_contraints_qualite, df_mp_dispo, df_mp_indispo = Separate_data(table_mp, df_mp, df_elmt_and_quality)

    # Suppression des matières premières indisponibles dans
    table_mp = clean_table_mp(table_mp, df_mp_indispo)

    # Construction de la matrice A et du vecteur C
    A, C = create_matrix_A_and_C(table_mp, df_mp_dispo)
    
    # Initialisation des listes pour les contraintes
    constraints = {'A_eq': {},'b_eq': {},'A_sup': {},'b_sup': {} }

    # Mettre  les contraintes concernant les éléments
    constraints = format_constraints_elements(df_contraints_element, A,constraints)

    # Mettre  les contraintes concernant la qualité
    constraints = format_constraints_qualite(df_contraints_qualite, A,constraints)

    # Mettre les contraintes concernant les matières premières disponibles
    constraints, bounds = format_constraints_MP(df_mp_dispo, constraints)


    # Résoudre le problème d'optimisation linéaire
    method = 'simplex' #'interior-point' 'simplex'
    coefficients = [0.6, 0.65,0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
    coefficients = [0.85, 0.9, 0.95]
    res, erreurs = optimize_with_correction(table_mp, C, constraints, bounds, method, coefficients)
    # res, erreurs = solve_linear_program(C, constraints, bounds,method)
    
    # Gestion du resultats
    gestion_resultats(erreurs, res, df_mp_dispo, table_mp, 
                      constraints, dossier_data, recette)
    
    return 
if __name__ == "__main__":
    # Vérifiez si un chemin de fichier Excel est fourni en argument
    if len(sys.argv) != 2:
        print("Usage: python main.py recipe_optimization_data")
        sys.exit(1)
    # Récupérez le chemin du fichier Excel à partir des arguments de ligne de commande
    chemin_fichier = abspath(sys.argv[1])

    # On recupere le chemin du dossier data
    dossier_data = os.path.dirname(chemin_fichier)
    # Suppression du vieux resultats
    remove_old_recipes(dossier_data)
    # Resolutions du nouveau probleme
    Recettes = [col for col in pd.read_excel(chemin_fichier, engine='calamine', sheet_name=2).columns if 'Unnamed' not in col]
    for recette in tqdm(Recettes, desc="Processing recipes", unit="recipe"):
        raw_material_table, mp_constraints, elmt_quality_constraints, errors= read_and_check_input_values(chemin_fichier)
        if errors :
            save_errors(errors, dossier_data,recette)
            break;
        create_optimal_recipe(recette, raw_material_table, mp_constraints,elmt_quality_constraints,dossier_data)
