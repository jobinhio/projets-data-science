import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import os




def compute_correlation(df, X_var, Y_var,plot=True, file_path=None):
    df_stat = df.loc[:, X_var + Y_var ]
    # Calculer la matrice de corrélation
    corr_matrix = df_stat.corr()
    # Supprimer les lignes et les colonnes contenant des valeurs NaN
    corr_matrix= corr_matrix.dropna(axis=0, how='all').dropna(axis=1, how='all')
    if plot:
        # Dessiner le heatmap
        sns.heatmap(np.round(corr_matrix, 2), annot=True, cmap="jet")

        # Sauvegarder le dessin
        if file_path :
            recipe_name = df.iloc[0]['Recette']
            # Chemin vers le dossier
            folder_path = os.path.join('..', 'Images', recipe_name)
            # Vérifier si le dossier existe, sinon le créer
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            path = os.path.join(folder_path, file_path)

            try:
                plt.savefig(path, dpi=600, bbox_inches="tight")
            except Exception as e:
                print("Error occurred while saving the image:", e)
    return corr_matrix

def compute_correlation(df, X_var, Y_var, plot=True, file_path=None):
    df_stat = df.loc[:, X_var + Y_var]
    # Calculer la matrice de corrélation
    corr_matrix = df_stat.corr()
    # Supprimer les lignes et les colonnes contenant des valeurs NaN
    corr_matrix = corr_matrix.dropna(axis=0, how='all').dropna(axis=1, how='all')
    
    if plot:
        # Spécifier la taille de l'image (largeur=10, hauteur=8 par exemple)
        plt.figure(figsize=(6, 8))
        # plt.figure(figsize=(6, 6))
        
        # Dessiner le heatmap
        sns.heatmap(np.round(corr_matrix, 2), annot=True, cmap="jet")

        # Sauvegarder le dessin
        if file_path:
            recipe_name = df.iloc[0]['Recette']
            # Chemin vers le dossier
            folder_path = os.path.join('..', 'Images', recipe_name)
            # Vérifier si le dossier existe, sinon le créer
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            path = os.path.join(folder_path, file_path)

            try:
                plt.savefig(path, dpi=600, bbox_inches="tight")
            except Exception as e:
                print("Error occurred while saving the image:", e)
    
    return corr_matrix


def compute_mean_absolute_correlation(df, X_var, Y_var):
    corr_matrix = compute_correlation(df, X_var, Y_var, plot=False)
    corr_matrix['Mean_Absolute_Correlation'] = sum(corr_matrix[col].abs() for col in Y_var) / len(Y_var)
    corr_matrix_sorted = corr_matrix.sort_values(by='Mean_Absolute_Correlation', ascending=False)
    X_var_list = corr_matrix_sorted.index.tolist()
    for y in Y_var:
        if y in X_var_list:
            X_var_list.remove(y)
    X_var_sorted = {var: corr_matrix_sorted.loc[var, 'Mean_Absolute_Correlation'] for var in X_var_list}
    
    return X_var_sorted

def print_correlation_results(Y_var, corr_matrix_sorted):
    msg = "Résultats de la corrélation entre"
    for i, y in enumerate(Y_var):
        if i < len(Y_var) - 1:
            msg += f" {y},"
        else:
            msg += f" {y} et les autres variables :"
    print(msg)
    
    for var, corr in corr_matrix_sorted.items():
        print('  ', f"{var}: {corr}")

