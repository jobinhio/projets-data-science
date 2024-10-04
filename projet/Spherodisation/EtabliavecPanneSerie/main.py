import sys
from os.path import abspath




from functions import  Simulation

# Test de la simulation
if __name__ == "__main__":
    chemin_BoutonsEtParamètres = 'BoutonsEtParamètres.CSV'
    chemin_ProgrammeDISA = 'ProgrammeDISA.CSV'
    chemin_ParamètresGénéraux = 'ParamètresGénéraux.CSV'


    # # Vérifiez si un chemin de fichier Excel est fourni en argument
    # if len(sys.argv) != 4:
    #     print("Usage: python main.py chemin_BoutonsEtParamètres chemin_ProgrammeDISA chemin_ParamètresGénéraux")
    #     sys.exit(1)
    # # Récupérez les chemin du fichier Excel à partir des arguments de ligne de commande
    # chemin_BoutonsEtParamètres = abspath(sys.argv[1])
    # chemin_ProgrammeDISA = abspath(sys.argv[2])
    # chemin_ParamètresGénéraux = abspath(sys.argv[3])

    sim = Simulation(chemin_ParamètresGénéraux, chemin_BoutonsEtParamètres, chemin_ProgrammeDISA)
    sim.run_simulation(1)  
