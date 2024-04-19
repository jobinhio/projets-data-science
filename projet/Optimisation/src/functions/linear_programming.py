from scipy.optimize import linprog

def solve_linear_program(C, A_ub, b_ub, A_eq, b_eq,bounds):
    # Résoudre le problème d'optimisation linéaire
    # res = linprog(C, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method ='interior-point',callback=linprog_terse_callback, options={'disp': True,'tol':0.0001})
    res = linprog(C, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method ='highs-ipm')
    res = linprog(C, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,bounds=bounds,  method ='interior-point')

    # Affichage du résultat
    print("Message :", res.message)
    print("Optimal solution:", res.x)
    print("Status :", res.status)
    print("Optimal value:", res.fun)

    # Vérifier si le problème admet une solution
    if res.success:
        print("Le problème admet une solution optimale.")
    else:
        print("Le problème n'admet pas de solution optimale.")
    return res