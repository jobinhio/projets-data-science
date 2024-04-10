import numpy as np
import pandas as pd

from functions.cleaning import concat_arrays


def format_constraints_elements(A_ub, b_ub,A_eq, b_eq,df_contraints, A):
  # Initialisation des listes pour les contraintes
  A_eq_list, b_eq_list, A_sup_list, b_sup_list, A_inf_list, b_inf_list = [], [], [], [], [], []

  # Parcours des données de contraintes
  for index, row in df_contraints.iterrows():
      if not pd.isna(row['Valeur visée']):
          A_eq_list.append(A[index])
          b_eq_list.append(row['Valeur visée'])

      if not pd.isna(row['Valeur Max par four']):
          A_sup_list.append(A[index])
          b_sup_list.append(row['Valeur Max par four'])

      if not pd.isna(row['Valeur Min par four']):
          A_inf_list.append(-A[index])
          b_inf_list.append(-row['Valeur Min par four'])

  # Conversion des listes en tableaux numpy
  A_eq_array, b_eq_array, A_sup_array, b_sup_array, A_inf_array, b_inf_array = map(np.array, (A_eq_list, b_eq_list, A_sup_list, b_sup_list, A_inf_list, b_inf_list))


  # Concaténation verticale
  A_ub, b_ub = concat_arrays(A_ub, b_ub, A_sup_array, b_sup_array)
  A_ub, b_ub = concat_arrays(A_ub, b_ub, A_inf_array, b_inf_array)
  A_eq, b_eq = concat_arrays(A_eq, b_eq, A_eq_array, b_eq_array)

  return A_ub, b_ub, A_eq, b_eq


def format_constraints_qualite(A_ub, b_ub,A_eq, b_eq,df_contraints, A):
  # Initialisation des listes pour les contraintes
  I = [ 0, 0, 0.44, 4.90, 0.37, 5.60, 0.37, 7.90, 39.00, 0, 0, 0, 0, 0, 4.40, 0, 0, 0]
  O = [ 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1 ]

  I_min, I_max= df_contraints.loc[0,'Impurété'],df_contraints.loc[2,'Impurété']
  O_min, O_max= df_contraints.loc[0,'ONO'],df_contraints.loc[2,'ONO']

  I_min, I, I_max = map(np.array, ([I_min], I, [I_max]))
  O_min, O, O_max = map(np.array, ([O_min], O, [O_max]))

  I_dot_A = I@A
  O_dot_A = O@A


  # Concaténation verticale
  A_ub, b_ub = concat_arrays(A_ub, b_ub, -1*I_dot_A, -1*I_min)
  A_ub, b_ub = concat_arrays(A_ub, b_ub, I_dot_A, I_max)
  A_ub, b_ub = concat_arrays(A_ub, b_ub, -1*O_dot_A, -1*O_min)
  A_ub, b_ub = concat_arrays(A_ub, b_ub, O_dot_A, O_max)

  return A_ub, b_ub, A_eq, b_eq


def format_constraints_MP(A_eq, b_eq,df_MP_dispo):
  # Les % de MP Min et Max
  bounds = []
  A_eq_MP, b_eq_MP = [],[]

  m = len(df_MP_dispo)

  # Contraintes sur les pourcentages sum(x_i) = 1
  A_eq_MP.append(np.ones(m))
  b_eq_MP.append(1)


  # Parcours des lignes du DataFrame
  for index, row in df_MP_dispo.iterrows():
      # Récupération des valeurs de "Part Min" et "Part Max", avec une valeur par défaut de 0 et 1 respectivement si elles sont manquantes
      part_min = row['Part Min'] if not pd.isna(row['Part Min']) else 0
      part_max = row['Part Max'] if not pd.isna(row['Part Max']) else 1
      # Ajout du tuple (Part Min, Part Max) à la liste bounds
      bounds.append((part_min, part_max))

      # Les % de MP à consommer
      part_a_consommer = row['Part à consommer']
      # Vérification si la valeur de "Part à consommer" est valide
      if not pd.isna(part_a_consommer):
        # Construction de A_eq_MP et b_eq_MP
          A_eq_tmp = np.zeros(m)
          A_eq_tmp[index] = 1
          A_eq_MP.append(A_eq_tmp)
          b_eq_MP.append(part_a_consommer)

  A_eq_array, b_eq_array = map(np.array, (A_eq_MP, b_eq_MP))
  A_eq, b_eq = concat_arrays(A_eq, b_eq, A_eq_array, b_eq_array)

  return A_eq, b_eq, bounds