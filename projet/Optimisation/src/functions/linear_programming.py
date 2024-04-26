from scipy.optimize import linprog

def solve_linear_program(C, A_ub, b_ub, A_eq, b_eq,bounds):
    # Résoudre le problème d'optimisation linéaire
    if ((A_ub.size == 0 | b_ub.size == 0 ) & (A_eq.size == 0 | b_eq.size == 0)) :
        res = linprog(C,bounds=bounds,  method ='highs',options={"presolve": False})
    elif (A_ub.size == 0 | b_ub.size == 0) :
        res = linprog(C, A_eq=A_eq, b_eq=b_eq,bounds=bounds, method ='highs',options={"presolve": False})
    elif (A_eq.size == 0 | b_eq.size == 0) :
        res = linprog(C, A_ub=A_ub, b_ub=b_ub,bounds=bounds, method ='highs',options={"presolve": False})
    else :
        res = linprog(C, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,bounds=bounds,  method ='highs',options={"presolve": False})
    return res
