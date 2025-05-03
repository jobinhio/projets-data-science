import sys
from os.path import abspath
import os
from tqdm import tqdm
import pandas as pd


from functions import Separate_data, clean_table_mp  
from functions import read_and_check_FDN_input_values, read_and_check_USB_input_values
from functions import create_matrix_A_and_C,format_constraints_elements
from functions import format_constraints_qualite, format_constraints_MP
from functions import optimize_with_correction
from functions import solve_linear_program
from functions import  remove_old_recipes
from functions import  gestion_resultats
from functions import  gestion_FDNresultats
def create_optimal_recipe(recette,table_mp, mp_constraints, elmt_quality_constraints,dossier):

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

    # Résolution de la formulation 1
    coefficients = [0.6, 0.65,0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
    coefficients = [0.85, 0.9, 0.95,1]
    res1, erreurs1 = optimize_with_correction(table_mp, C, constraints, bounds, method, coefficients)
    
    # Résolution de la formulation 2
    res2, erreurs2 = solve_linear_program(C, constraints, bounds,method)
    
    # # Gestion du resultats USB
    # gestion_resultats(erreurs1, res1, erreurs2, res2, 
    #                   df_mp_dispo, table_mp, constraints, dossier, recette)
    
    # Gestion du resultats pour FDN
    gestion_FDNresultats(erreurs1, res1, erreurs2, res2, df_mp_dispo, table_mp, constraints, dossier, recette)

    return 
if __name__ == "__main__":
    # Vérifiez si un chemin de fichier Excel est fourni en argument
    if len(sys.argv) != 3:
        print("Usage: python main.py InputsOutputs recette")
        sys.exit(1)
    # Récupérez le chemin du fichier Excel à partir des arguments de ligne de commande
    dossier_InputsOutputs = abspath(sys.argv[1])
    recette = sys.argv[2]
    # Suppression du vieux resultats
    remove_old_recipes(dossier_InputsOutputs)

    # Vérifications des données d'entrée
    table_mp, mp_constraints, elmt_quality_constraints, errors= read_and_check_FDN_input_values(dossier_InputsOutputs,recette)

    # Resolutions du nouveau probleme 1 et 2
    if not errors :
        create_optimal_recipe(recette, table_mp, mp_constraints,elmt_quality_constraints,dossier_InputsOutputs)
