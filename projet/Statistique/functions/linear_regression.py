import numpy as np
import plotly.graph_objects as go
import statsmodels.api as sm
from statsmodels.sandbox.regression.predstd import wls_prediction_std
from scipy.stats import t
import os



def linear_regression_with_predict_intervals(df, x_name, y_name, alpha=0.05, width=1.96):
    """
    Réalise une régression linéaire et calcule les intervalles de prédiction.

    Args:
    - df : DataFrame contenant les données
    - x_name : Nom de la colonne représentant la variable indépendante
    - y_name : Nom de la colonne représentant la variable dépendante
    - alpha : Niveau de confiance pour les intervalles de confiance (par défaut : 0.05)
    - confidence_interval_width : Largeur de l'intervalle de confiance (par défaut : 1.96 pour un niveau de confiance de 95 %)

    Returns:
    - ypred : Prédictions du modèle
    - pred_low : Limite inférieure de l'intervalle de prédictions
    - pred_high : Limite supérieure de l'intervalle de prédictions
    """

    df = df.loc[:, ['Recette','Rm [MPA]', 'Moyenne allongement [%]', 'Impureté [%]', 'Ferrite [%]', 'Purete ONO [%]', 'Purete THIELMANN [%]','Purete MAYER [%]', 'C [%]', 'Si [%]', 'Mn [%]', 'Cu [%]', 'Cr [%]', 'P [%]', 'Ni [%]', 'Mo [%]', 'Sn [%]', 'Sb [%]', 'Al [%]', 'S [%]', 'Mg [%]', 'Pb [%]', 'Ti [%]', 'As [%]', 'Bi [%]', 'V [%]']]
    # Sélectionner les données
    x = df[x_name]
    y = df[y_name]

    # Ajouter une colonne de biais à x pour le modèle linéaire
    x_ext = sm.add_constant(x)

    # Créer le modèle linéaire
    model = sm.OLS(y, x_ext)

    # Fitter le modèle
    results = model.fit()

    # Prédire les valeurs de y
    ypred = results.predict(x_ext)

    # Calculer l'erreur standard pour les prédictions
    predict_se, _, _ = wls_prediction_std(results, alpha=alpha)

    # Calculer les bornes inférieures et supérieures des intervalles de confiance
    predict_ci_low = ypred - predict_se * width
    predict_ci_upp = ypred + predict_se * width

    return ypred, predict_ci_low, predict_ci_upp


def plot_linear_regression_with_predict_intervals(df,x_name, y_name, width,file_path=None):
    """
    Crée une figure Plotly avec les données observées, la régression linéaire et l'intervalle de prédiction.

    Args:
    - x_val : Valeurs de la variable indépendante
    - y_val : Valeurs de la variable dépendante
    - ypred : Prédictions du modèle
    - pred_low : Limite inférieure de l'intervalle de confiance des prédictions
    - pred_high : Limite supérieure de l'intervalle de confiance des prédictions
    - x_name : Nom de la variable indépendante (axe x)
    - y_name : Nom de la variable dépendante (axe y)
    - save_path : Chemin de sauvegarde de l'image (facultatif)
    """

    x_val,y_val = df[x_name],df[y_name]
    ypred, pred_low, pred_high = linear_regression_with_predict_intervals(df, x_name, y_name,width)
    # Créer la figure Plotly
    fig = go.Figure()

    # Ajouter les données observées
    fig.add_trace(go.Scatter(x=x_val, y=y_val, mode='markers', name='Données'))

    # Ajouter la régression linéaire
    fig.add_trace(go.Scatter(x=x_val, y=ypred, mode='lines', name='Régression linéaire', line=dict(color='red')))

    # Ajouter l'intervalle de confiance
    fig.add_trace(go.Scatter(x=np.concatenate([x_val, x_val[::-1]]),
                             y=np.concatenate([pred_low, pred_high[::-1]]),
                             fill='toself',
                             name='Intervalle de confiance'))

    # Mise en forme du graphique
    fig.update_layout(title='Régression linéaire avec intervalle de confiance',
                      xaxis_title=x_name,
                      yaxis_title=y_name)

    fig.show()
    # Sauvegarder l'image
    if file_path :
        recipe_name = df.iloc[0]['Recette']
        # Chemin vers le dossier
        folder_path = r'..\Images\\' + recipe_name
        # Vérifier si le dossier existe, sinon le créer
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        path = os.path.join(folder_path, file_path)
        
        try:
            fig.write_image(path, format='pdf', scale=2)
        except Exception as e:
            print("Error occurred while saving the image:", e)
    return 




def compute_confidence_interval(df, column, confidence=0.95):
    """
    Compute the confidence interval for a given column in a DataFrame.

    Parameters:
    df (DataFrame): The DataFrame containing the data.
    column (str): The name of the column for which to compute the confidence interval.
    confidence (float): The confidence level for the interval (default is 0.95).

    Returns:
    tuple: A tuple containing the lower and upper bounds of the confidence interval.
    """
    data = df[column]
    n = len(data)

    mean = np.mean(data)
    std_err = np.std(data, ddof=1) / np.sqrt(n)  # Standard error of the mean
    t_value = t.ppf((1 + confidence) / 2, n - 1)  # T-score for the given confidence level and degrees of freedom

    lower_bound = mean - t_value * std_err
    upper_bound = mean + t_value * std_err

    return lower_bound, upper_bound