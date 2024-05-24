from scipy.optimize import linprog
import numpy as np

def solver(C, A_ub, b_ub, A_eq, b_eq, bounds, method):
    if A_ub.size > 0 and b_ub.size > 0:
        # Nombre de variables de décision
        n = len(C)
        m = A_ub.shape[0]

        # Transformation des contraintes Ax < b en Ax + s = b
        A_ub_transformed = np.hstack((A_ub, np.eye(m)))
        b_ub_transformed = b_ub

        # Concaténation avec les contraintes d'égalité existantes
        if A_eq.size > 0 and b_eq.size > 0:
            A_eq_combined = np.vstack((np.hstack((A_eq, np.zeros((A_eq.shape[0], m)))), A_ub_transformed))
            b_eq_combined = np.concatenate((b_eq, b_ub_transformed))
        else:
            A_eq_combined = A_ub_transformed
            b_eq_combined = b_ub_transformed

        # Bornes des variables de décision
        bounds_x = bounds

        # Bornes des variables d'écart (0 < s_i < inf)
        bounds_s = [(0, None) for _ in range(m)]

        # Concaténation des bornes pour former les bornes totales
        bounds_combined = bounds_x + bounds_s


        # Nouvelle fonction objectif pour maximiser la somme des variables d'écart
        # Minimiser -s équivaut à maximiser s
        C_combined = np.concatenate([C, -np.ones(m)])

    else:
        # Si aucune contrainte Ax < b n'est donnée, n'effectuez pas la transformation
        A_eq_combined = A_eq
        b_eq_combined = b_eq
        bounds_combined = bounds
        C_combined = C

    # Résoudre le problème d'optimisation linéaire
    res = linprog(C_combined, A_eq=A_eq_combined, b_eq=b_eq_combined, bounds=bounds_combined, method=method, options={"presolve": False})

    return res

def check_constraints_condition(res, tol=1e-4):
    ce_residuals = res.con
    ce_result = [1 if abs(val) <= tol else 0 for val in ce_residuals]
    return ce_result

def find_errors(ce_result, constraints):
    """
    Trouve les errors dans les résultats des contraintes.

    Cette fonction vérifie les résultats des contraintes et ajoute des messages d'erreur
    aux errors existantes en cas de résultats incorrects.

    Paramètres :
        ce_result (array_like) : Résultats des contraintes d'égalité.
        ci_result (array_like) : Résultats des contraintes d'inégalité.
        constraints (dict) : Dictionnaire contenant les contraintes.
        errors (list) : Liste des errors existantes.

    Returns:
        list : Liste mise à jour des errors.
    """

    errors = []

    # Vérification des contraintes d'égalité (b_eq)
    b_eq = constraints['b_eq'] 
    b_eq_keys = list(b_eq.keys())
    ce_erros =  {}
    for key, value in zip(b_eq_keys, ce_result):
        if value == 0 :
            ce_erros [key] = b_eq [key]
            message = f"Veuillez revoir la valeur de '{key}' : {b_eq [key]}"
            errors.append(message)


    # Vérification des contraintes d'inégalité (b_ub)
    b_ub = constraints['b_sup']  
    b_ub_keys = list(b_ub.keys())
    ci_erros =  {}
    for key, value in zip(b_ub_keys, ce_result[len(b_eq_keys):]):
        if value == 0 and  key.endswith('_max') :
            ci_erros [key] = value
            error_name, error_value = key.split('_')
            message = f"Veuillez revoir la valeur {error_value} de {error_name}"
            errors.append(message)
    return errors

def solve_linear_program(C, constraints, bounds,method):
    A_ub= np.array(list(constraints['A_sup'].values()))
    A_eq = np.array(list(constraints['A_eq'].values()))
    b_ub = np.array(list(constraints['b_sup'].values()))
    b_eq = np.array(list(constraints['b_eq'].values()))
    res  = solver(C, A_ub, b_ub, A_eq, b_eq, bounds,method)  
    ce_result = check_constraints_condition(res, tol=1e-4)

    erreurs = find_errors(ce_result, constraints)
    return  res, erreurs