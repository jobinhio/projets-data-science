from scipy.optimize import linprog
import numpy as np

def solver(C, A_ub, b_ub, A_eq, b_eq, bounds,method):
    # Résoudre le problème d'optimisation linéaire
    if (A_ub.size == 0 or b_ub.size == 0) and (A_eq.size == 0 or b_eq.size == 0):
        res = linprog(C, bounds=bounds,method = method, options={"presolve": False}) #False
    elif A_ub.size == 0 or b_ub.size == 0:
        res = linprog(C, A_eq=A_eq, b_eq=b_eq, bounds=bounds,method = method, options={"presolve": False}) #False
    elif A_eq.size == 0 or b_eq.size == 0:
        res = linprog(C, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method = method, options={"presolve": False}) #False
    else:
        res = linprog(C, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds,method = method, options={"presolve": False}) #False
    return res

def check_constraints_condition(res, tol=1e-4):
    ce_residuals, ci_residuals = res.con, res.slack
    ci_result = [1 if val > 0 or abs(val) <= tol else 0 for val in ci_residuals]
    ce_result = [1 if abs(val) <= tol else 0 for val in ce_residuals]
    return ce_result, ci_result

def solve_linear_program(C, constraints, bounds,method):
    A_ub= np.array(list(constraints['A_sup'].values()))
    A_eq = np.array(list(constraints['A_eq'].values()))
    b_ub = np.array(list(constraints['b_sup'].values()))
    b_eq = np.array(list(constraints['b_eq'].values()))

    print("A_eq = ", A_eq)
    print("b_eq = ", b_eq)
    res  = solver(C, A_ub, b_ub, A_eq, b_eq, bounds,method)  
    ce_result, ci_result = check_constraints_condition(res, tol=1e-4)
    return  res,  ce_result, ci_result


def count_zeros(df_table):
    """
    Compte le nombre de zéros dans chaque colonne du dataframe.

    Cette fonction compte le nombre de zéros dans chaque colonne du dataframe donné.

    Paramètres :
        df_table (DataFrame) : Le dataframe dans lequel compter les zéros.

    Renvois :
        dict : Un dictionnaire contenant le compte des zéros pour chaque colonne.
    """
    zero_counts = {}
    for column in df_table.columns[1:]:
        zero_counts[column + '_max'] = (df_table[column] == 0).sum()
    return zero_counts

def reduce_max_values_b_ub(b_ub, zero_counts, coeff):
    """
    Réduit la limite supérieure des contraintes en fonction du coefficient donné et du nombre de zéros.

    Cette fonction réduit la limite supérieure des contraintes en fonction du coefficient donné
    et du nombre de zéros dans chaque colonne, puis effectue une vérification entre les limites
    supérieures et inférieures pour s'assurer de leur cohérence.

    Paramètres :
        b_ub (dict) : Dictionnaire des limites supérieures des contraintes.
        zero_counts (dict) : Dictionnaire contenant le nombre de zéros pour chaque colonne.
        coeff (float) : Coefficient de réduction à appliquer.

    Returns:
        dict : Le dictionnaire des limites supérieures des contraintes réduit.
    """

    # Pour le Si et le C on prend la moyenne comme maximun
    b_ub['Si_max'] = (b_ub['Si_max'] + abs(b_ub['Si_min']))/2 
    b_ub['C_max'] = (b_ub['C_max'] + abs(b_ub['C_min']))/2 
    for key, _ in zero_counts.items():
        if key in b_ub and  (key not in ['Si_max','C_max']) :
            b_ub[key] *= coeff

    for key, value in b_ub.items():
        if key.endswith('_max') and key.replace('_max', '_min') in b_ub and  (key not in ['Si_max','C_max']):
            min_key = key.replace('_max', '_min')
            if abs(b_ub[min_key]) > b_ub[key]:
                b_ub[key] = abs(b_ub[min_key])
    return b_ub


def remove_max_key(zero_counts):
    """
    Supprime la clé avec la valeur maximale dans le dictionnaire zero_counts.

    Cette fonction supprime la clé avec la valeur maximale dans le dictionnaire zero_counts.
    Si le dictionnaire est vide, elle renvoie None.

    Paramètres :
        zero_counts (dict) : Dictionnaire contenant le nombre de zéros pour chaque colonne.

    Returns:
        dict or None : Le dictionnaire mis à jour sans la clé avec la valeur maximale, ou None si le dictionnaire est vide.
    """
    if not zero_counts:
        return None
    max_key = max(zero_counts, key=zero_counts.get)
    zero_counts.pop(max_key)
    return zero_counts


def find_errors(ce_result, ci_result, constraints):
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
    # Vérification des contraintes d'inégalité (b_ub)
    b_ub = constraints['b_sup']  
    b_ub_keys = list(b_ub.keys())
    ci_erros =  {}
    for key, value in zip(b_ub_keys, ci_result):
        if value == 0 and  key.endswith('_max') :
            ci_erros [key] = value
            error_name, error_value = key.split('_')
            message = f"Veuillez revoir la valeur {error_value} de {error_name}"
            errors.append(message)

    # Vérification des contraintes d'égalité (b_eq)
    b_eq = constraints['b_eq'] 
    b_eq_keys = list(b_eq.keys())
    ce_erros =  {}
    for key, value in zip(b_eq_keys, ce_result):
        if value == 0 :
            ce_erros [key] = b_eq [key]
            message = f"Veuillez revoir la valeur de '{key}' : {b_eq [key]}"
            errors.append(message)
    return errors


def optimize_with_correction(df_table, C, constraints, bounds, method, coefficients):
    """
    Optimize with coefficients.

    This function optimizes with coefficients and returns the result and errors.

    Parameters:
        df_table (DataFrame): The dataframe table.
        C (array_like): Coefficients of the linear objective function.
        constraints (dict): Constraints of the linear optimization problem.
        bounds (tuple): Bounds of the decision variables.
        method (str): Method used for solving the linear optimization problem.
        coefficients (array_like): Coefficients for optimization.

    Returns:
        tuple: Result and errors.

    """
    zero_counts = count_zeros(df_table)
    # print(zero_counts)
    errors = []

    b_ub_true = constraints['b_sup']
    
    All_errors = []
    res = None
    while zero_counts :
        for coeff in coefficients:
            b_ub = b_ub_true.copy()
            # On reduit les valeurs maximales de b_ub d'un facteur coeff
            constraints['b_sup'] = reduce_max_values_b_ub(b_ub, zero_counts, coeff)
            # On reduit le problème linéaire avec une les nouvelles contraintes maximales 
            res, ce_result, ci_result = solve_linear_program(C, constraints, bounds, method)
            constraints['b_sup'] = b_ub_true.copy()
            # On vérifie que la solution obtenu respecte les contraintes de base
            errors = find_errors(ce_result, ci_result, constraints)
            All_errors += errors
            # print(errors)
            # print(f"Méthode: {method}\nCoefficients: {coeff}\nRésultats CE: {ce_result}\nRésultats CI: {ci_result}\n")
            if not errors:
                return res, errors

        zero_counts = remove_max_key(zero_counts)
        # print(f"Colonnes restantes à vérifier : {zero_counts}")
    return res, list(set(All_errors))

