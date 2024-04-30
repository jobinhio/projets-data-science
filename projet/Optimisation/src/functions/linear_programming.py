from scipy.optimize import linprog
import numpy as np

def call_solver(C, A_ub, b_ub, A_eq, b_eq, bounds,method):
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
    res  = call_solver(C, A_ub, b_ub, A_eq, b_eq, bounds,method)  
    ce_result, ci_result = check_constraints_condition(res, tol=1e-4)
    return  res,  ce_result, ci_result

