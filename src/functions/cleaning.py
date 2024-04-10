import numpy as np

def concat_arrays(matrix_main, vector_main, matrix_to_concat, vector_to_concat):
    """
    Concatène les matrices 'matrix_to_concat' et les vecteurs 'vector_to_concat' à 'matrix_main' et 'vector_main' respectivement.

    Args:
    matrix_main (numpy.ndarray): Matrice numpy à laquelle concaténer 'matrix_to_concat'.
    vector_main (numpy.ndarray): Vecteur numpy à concaténer avec 'vector_to_concat'.
    matrix_to_concat (numpy.ndarray): Matrice numpy à concaténer avec 'matrix_main'.
    vector_to_concat (numpy.ndarray): Vecteur numpy à concaténer avec 'vector_main'.

    Returns:
    numpy.ndarray: La matrice résultante après la concaténation de 'matrix_to_concat' à 'matrix_main'.
    numpy.ndarray: Le vecteur résultant après la concaténation de 'vector_to_concat' à 'vector_main'.
    """
    if len(matrix_main) == 0:
        matrix_main = matrix_to_concat
        vector_main = vector_to_concat
    else:
        matrix_main = np.vstack((matrix_main, matrix_to_concat))
        vector_main = np.concatenate((vector_main, vector_to_concat))

    return matrix_main, vector_main
