import sys
from os.path import abspath
import os
from tqdm import tqdm
import time
# Chemin du dossier src
chemin_src = os.path.join('.', 'src')
sys.path.append(chemin_src)


from functions import Separate_data, nettoyer_dataframe 
from functions import read_and_check_input_values 
from functions import construire_tableau
from functions import format_constraints_elements, format_constraints_qualite, format_constraints_MP
from functions import optimize_with_correction
from functions import  construct_result_dataframe,export_result,save_errors,remove_old_resultats
def create_optimal_recipe(recette,Tableau_Matiere_Element, contraintes_mp, contraintes_elmt_and_quality,dossier_data):
    df_mp, df_elmt_and_quality = contraintes_mp[recette], contraintes_elmt_and_quality[recette]

    df_contraints_element, df_contraints_qualite, df_MP_dispo, df_MP_indispo = Separate_data(Tableau_Matiere_Element, df_mp, df_elmt_and_quality)

    # Suppression des matières premières indisponibles
    Tableau_Matiere_Element = nettoyer_dataframe(Tableau_Matiere_Element, df_MP_indispo)

    # Construction de la matrice A et du vecteur C
    A, C = construire_tableau(Tableau_Matiere_Element, df_MP_dispo)

    # Initialisation des listes pour les contraintes
    constraints = {'A_eq': {},'b_eq': {},'A_sup': {},'b_sup': {} }

    # Mettre  les contraintes concernant les éléments
    constraints = format_constraints_elements(df_contraints_element, A,constraints)

    # Mettre  les contraintes concernant la qualité
    constraints = format_constraints_qualite(df_contraints_qualite, A,constraints)

    # Mettre les contraintes concernant les matières premières disponibles
    constraints, bounds = format_constraints_MP(df_MP_dispo, constraints)

    # Résoudre le problème d'optimisation linéaire
    method = 'simplex' #'interior-point' 'simplex'
    coefficients = [0.6, 0.65,0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
    res, erreurs = optimize_with_correction(Tableau_Matiere_Element, C, constraints, bounds, method, coefficients)

    # Gestion du resultats
    if not erreurs: 
        # Construire le DataFrame résultats
        df_res,contraints_res = construct_result_dataframe(res, df_MP_dispo, Tableau_Matiere_Element,constraints)
        # Écrire le DataFrame résultats dans le fichier Excel
        export_result(df_res, dossier_data, new_sheet_name= recette)
        print("Le problème pour la recette" ,recette,"admet une solution.")

    else :
        # Sauvegarder les erreurs dans un fichier texte
        save_errors(erreurs, dossier_data,recette)
        print("Les erreurs du problème " ,recette," ont été enregistrées dans un fichier")
    return 

if __name__ == "__main__":
    # Vérifiez si un chemin de fichier Excel est fourni en argument
    if len(sys.argv) != 2:
        print("Usage: python main.py chemin_vers_fichier_excel")
        sys.exit(1)
    # Récupérez le chemin du fichier Excel à partir des arguments de ligne de commande
    chemin_fichier = abspath(sys.argv[1])

    # On recupere le chemin du dossier data
    dossier_data = os.path.dirname(chemin_fichier)
    # Suppression du vieux resultats
    remove_old_resultats(dossier_data)
    # Resolutions du nouveau probleme
    Recettes = ['GS 400-15','GS 450-10','GS 500-7','GS 600-3']
    for recette in tqdm(Recettes, desc="Processing recipes", unit="recipe"):
        raw_material_table, mp_constraints, elmt_quality_constraints, errors= read_and_check_input_values(chemin_fichier)
        if errors :
            save_errors(errors, dossier_data,recette)
            break;
        create_optimal_recipe(recette, raw_material_table, mp_constraints,elmt_quality_constraints,dossier_data)
        time.sleep(0.1)  # Simulate time delay