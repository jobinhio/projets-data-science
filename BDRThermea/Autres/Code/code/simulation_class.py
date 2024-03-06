from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
import numpy as np
import pandas as pd
import os

from deap import base, creator, tools, algorithms
import time
import multiprocessing

import time
from timeout_decorator import timeout, TimeoutError



class HeatPumpSimulator:
    def __init__(self, fmu_filename, start_time=0.0, stop_time=1500.0, step_size=1.0):
        self.fmu_filename = fmu_filename
        self.start_time = start_time
        self.stop_time = stop_time
        self.step_size = step_size
        self.model_description = read_model_description(fmu_filename)
        self.vr = {
            variable.name: variable.valueReference for variable in self.model_description.modelVariables}
        self.unzip_directory = self.prepare_fmu()

    def prepare_fmu(self):
        notebook_dir = os.path.dirname(os.path.abspath("__file__"))

        # Construisez le chemin absolu du fichier FMU à partir du chemin relatif
        fmu_absolute_path = os.path.join(notebook_dir, self.fmu_filename)

        fmu_directory = os.path.dirname(fmu_absolute_path)
        unzip_directory = os.path.join(fmu_directory, 'unzip')
        os.makedirs(unzip_directory, exist_ok=True)
        extract(fmu_absolute_path, unzipdir=unzip_directory)

        return unzip_directory

    PARAM_RANGES = {
        'x_areaLeakage': (1e-8, 1e-6),
        'x_areaSuctionValve': (2e-6, 1e-3),
        'x_areaDischargeValve': (1e-7, 1e-4),
        'x_relativeDeadSpace': (0.001, 0.1),
        'x_driveEfficiency': (0.85, 0.98)
    }

    def verify_parameter_ranges(self, start_values):
        for param, value in start_values.items():
            if param in self.PARAM_RANGES:
                min_val, max_val = self.PARAM_RANGES[param]
                if not min_val <= value <= max_val:
                    raise ValueError(
                        f"Value of {param} ({value}) is out of range [{min_val}, {max_val}]")


    def simulate2(self, start_values, show_plot=False):
        fmu = FMU2Slave(guid=self.model_description.guid,
                        modelIdentifier=self.model_description.coSimulation.modelIdentifier,
                        unzipDirectory=self.unzip_directory)
        self.verify_parameter_ranges(start_values)
        try:
            fmu.instantiate()
            self.setup_simulation(fmu, start_values)

            # Utilisation d'une file pour récupérer les résultats du processus
            results_queue = multiprocessing.Queue()
            process = multiprocessing.Process(target=self.run_simulation, args=(fmu, results_queue))

            # Démarrage du processus
            process.start()

            # Mesurer le temps d'exécution de la simulation
            start_time = time.time()
            time_arret = 15 #180 #15
            process.join(timeout=time_arret)  # Attendre au maximum time_arret secondes 
            end_time = time.time()
            execution_time = end_time - start_time

            # Récupérer les résultats du processus ou si le processus s'arrete à cause d'une erreur
            # alors terminer le processus 
            # Récupérer les résultats du processus
            if process.is_alive():
                print(f"Le temps d'exécution dépasse {time_arret} secondes. Tentative d'arrêt du processus.")
                process.terminate()
                process.join()
                results = {}
            else:
                # Vérifier le code de sortie du processus fils
                exit_code = process.exitcode

                if exit_code != 0:
                    print(f"Le processus fils s'est terminé avec le code de sortie {exit_code}.")
                    results = {}
                else :
                    results = results_queue.get()

            if show_plot:
                self.plot_results(results)

        finally:
            fmu.terminate()
            fmu.freeInstance()

        return results
   
    def run_simulation2(self, fmu,results_queue):
        time = np.arange(self.start_time, self.stop_time, self.step_size)
        output_vrs = ['y_T_out', 'y_heatPower', 'y_elecPower', 'y_COP']
        results = {var: [] for var in output_vrs}
        results['time'] = []

        for t in time:
            fmu.doStep(currentCommunicationPoint=t,
                       communicationStepSize=self.step_size)
            output_values = fmu.getReal([self.vr[var] for var in output_vrs])
            for i, var in enumerate(output_vrs):
                results[var].append(output_values[i])
            results['time'].append(t)

        results_queue.put(results)

        return results



    def simulate(self, start_values, show_plot=False):
        fmu = FMU2Slave(guid=self.model_description.guid,
                        modelIdentifier=self.model_description.coSimulation.modelIdentifier,
                        unzipDirectory=self.unzip_directory)
        self.verify_parameter_ranges(start_values)
        time_arret = 15 #180 #15

        try:
            # Utiliser @timeout uniquement pour la fonction run_simulation(fmu)
            fmu.instantiate()
            self.setup_simulation(fmu, start_values)
            results = self.run_simulation(fmu)
        except TimeoutError:
            print(f"Le temps d'exécution dépasse {time_arret} secondes.\n")
            results = {}

        except Exception as e:
            print(f"Une autre erreur a été détectée : {type(e).__name__}")
            results = {}

        finally:
            fmu.terminate()
            fmu.freeInstance()

        return results


    def setup_simulation(self, fmu, start_values):
        fmu.setupExperiment(startTime=self.start_time)
        for var_name, start_value in start_values.items():
            fmu.setReal([self.vr[var_name]], [start_value])
        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

    ## on oblige la simulation à durer moins de 15 secondes
    @timeout(15, use_signals=False)
    def run_simulation(self, fmu):
        time = np.arange(self.start_time, self.stop_time, self.step_size)
        output_vrs = ['y_T_out', 'y_heatPower', 'y_elecPower', 'y_COP']
        results = {var: [] for var in output_vrs}
        results['time'] = []

        for t in time:
            fmu.doStep(currentCommunicationPoint=t,
                       communicationStepSize=self.step_size)
            output_values = fmu.getReal([self.vr[var] for var in output_vrs])
            for i, var in enumerate(output_vrs):
                results[var].append(output_values[i])
            results['time'].append(t)

        return results
    
    def critere_erreur(self,start_values, finish_values):

        resultats = self.simulate(start_values)

        # Si la simulation échoue alors l'erreur prend une très grand valeur (infinie)
        erreur = 10000

        # Sinon on calcul l'erreur 
        if bool(resultats):
            #COP
            Fmu_COP = resultats['y_COP'] [-1]
            True_COP = finish_values['y_COP']

            #Puissances 
            Fmu_heatPower = resultats['y_heatPower'] [-1]
            True_heatPower = finish_values['y_heatPower']

            Fmu_elecPower = resultats['y_elecPower'] [-1]
            True_elecPower = finish_values['y_elecPower']

            # print("Fmu_COP", Fmu_COP)
            # print("True_COP", True_COP)
            erreur = abs(True_COP-Fmu_COP) + abs(True_heatPower-Fmu_heatPower) + abs(True_elecPower-Fmu_elecPower)
            print("erreur absolue :",erreur)

        return erreur
    
    def objective (self,x,INPUT,OUTPUT):
        res = 0

        # Evaluate the objective function using the simulator
        n_train = len(INPUT['u_T_watrer_in'])
        # n = 5
        # n = 5

        print("x :",x,"\n")

        # Pour chaque ligne des données Train
        for i in range(n_train):
            print("i_train  =",i)
            start_values = {
                'u_compressorFrequency': INPUT['u_compressorFrequency'].iloc[i],
                'u_VFlow': INPUT['u_VFlow'].iloc[i],
                'u_T_watrer_in': INPUT['u_T_watrer_in'].iloc[i],
                'u_T_air': INPUT['u_T_air'].iloc[i],
                # Valeurs fixes des paramètres pour l'instant
                'x_areaLeakage': x[0],
                'x_areaSuctionValve': x[1],
                'x_areaDischargeValve': x[2],
                'x_relativeDeadSpace': x[3],
                'x_driveEfficiency': x[4]
            }
            finish_values = {
                'Water_out' : OUTPUT['Water_out'].iloc[i],
                'y_heatPower': OUTPUT['y_heatPower'].iloc[i],  
                'y_elecPower': OUTPUT['y_elecPower'].iloc[i],
                'y_COP': OUTPUT['y_COP'].iloc[i]
            }
            # print(start_values)
            differences = self.critere_erreur(start_values, finish_values)

            # Ajouter differences à res uniquement si differences n'est pas -1
            if differences != -1:
                res += differences
        return res

        
    def objective (self,x,INPUT,OUTPUT):
        res = 0

        # Evaluate the objective function using the simulator
        n_train = len(INPUT['u_T_watrer_in'])
        # n = 5
        # n = 5

        print("x :",x,"\n")

        # Pour chaque ligne des données Train
        for i in range(n_train):
            print("i_train  =",i)
            start_values = {
                'u_compressorFrequency': INPUT['u_compressorFrequency'].iloc[i],
                'u_VFlow': INPUT['u_VFlow'].iloc[i],
                'u_T_watrer_in': INPUT['u_T_watrer_in'].iloc[i],
                'u_T_air': INPUT['u_T_air'].iloc[i],
                # Valeurs fixes des paramètres pour l'instant
                'x_areaLeakage': x[0],
                'x_areaSuctionValve': x[1],
                'x_areaDischargeValve': x[2],
                'x_relativeDeadSpace': x[3],
                'x_driveEfficiency': x[4]
            }
            finish_values = {
                'Water_out' : OUTPUT['Water_out'].iloc[i],
                'y_heatPower': OUTPUT['y_heatPower'].iloc[i],  
                'y_elecPower': OUTPUT['y_elecPower'].iloc[i],
                'y_COP': OUTPUT['y_COP'].iloc[i]
            }
            # print(start_values)
            differences = self.critere_erreur(start_values, finish_values)

            # Ajouter differences à res uniquement si differences n'est pas -1
            if differences != -1:
                res += differences
        return res

    
    def plot_results(self, results):
            pass








##### test 
        

# Spécifiez le chemin du fichier Excel
chemin_fichier_excel = '/home/congo/BDRThermea/2023-m2-bdrthermea/multi-physics-modeling/data/Inputdata.xlsx'
df_input = pd.read_excel(chemin_fichier_excel)


chemin_fichier_excel = '/home/congo/BDRThermea/2023-m2-bdrthermea/multi-physics-modeling/data/Outputdata.xlsx'
df_output = pd.read_excel(chemin_fichier_excel)


df_no_defrosts = df_input[df_input['Defrosts'] == 'no']

OUTPUT = {
    'Water_out' : df_output['Water_out'],
    'y_heatPower': df_output['y_heatPower'],  
    'y_elecPower': df_output['y_elecPower'],
    'y_COP': df_output['y_COP']
}

INPUT = {
    'u_compressorFrequency': df_no_defrosts['Frequency'],
    'u_VFlow': df_no_defrosts['Flow'],
    'u_T_watrer_in': df_no_defrosts['Water_in'],
    'u_T_air': df_no_defrosts['T_air'],
    'x_areaLeakage': 5e-7,
    'x_areaSuctionValve': 5e-4,
    'x_areaDischargeValve': 5e-5,
    'x_relativeDeadSpace': 0.05,
    'x_driveEfficiency': 0.9
}

        
import numpy as np
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.algorithms.soo.nonconvex.ga import GA

import numpy as np
from pymoo.core.problem import ElementwiseProblem

class MyProblem(ElementwiseProblem):

    def __init__(self):
        super().__init__(n_var=5,
                         n_obj=1,
                        #  n_obj=2,
                         n_ieq_constr=2,
                         xl=np.array([1e-8, 2e-6,1e-7 , 0.001, 0.85]),
                         xu=np.array([1e-6,1e-3,1e-4 ,0.1,0.98]))

    def _evaluate(self, x, out, *args, **kwargs):
        simulator = HeatPumpSimulator('../FMU/HPFMU_20_Linux.fmu')

        res = 0

        # Evaluate the objective function using the simulator
        # n = 5
        n_train = len(INPUT['u_T_watrer_in'])
    
        
        print("x :",x,"\n")

        for i in range(n_train):
            print("i_train = ",i,"\n")

            start_values = {
                'u_compressorFrequency': INPUT['u_compressorFrequency'].iloc[i],
                'u_VFlow': INPUT['u_VFlow'].iloc[i],
                'u_T_watrer_in': INPUT['u_T_watrer_in'].iloc[i],
                'u_T_air': INPUT['u_T_air'].iloc[i],
                # Valeurs fixes des paramètres pour l'instant
                'x_areaLeakage': x[0],
                'x_areaSuctionValve': x[1],
                'x_areaDischargeValve': x[2],
                'x_relativeDeadSpace': x[3],
                'x_driveEfficiency': x[4]
            }
            finish_values = {
                'Water_out' : OUTPUT['Water_out'].iloc[i],
                'y_heatPower': OUTPUT['y_heatPower'].iloc[i],  
                'y_elecPower': OUTPUT['y_elecPower'].iloc[i],
                'y_COP': OUTPUT['y_COP'].iloc[i]
            }
            # print(start_values)
            differences = simulator.critere_erreur(start_values, finish_values)
            
            # Ajouter differences à res uniquement si differences n'est pas -1
            if differences != -1:
                res += differences

        out["F"] = [res]






from pymoo.problems.functional import FunctionalProblem



def main():
    # Définir la fonction objectif 
    chemin_fmu = '/home/congo/BDRThermea/2023-m2-bdrthermea/multi-physics-modeling/FMU/HPFMU_20_Linux.fmu'
    simulator = HeatPumpSimulator(chemin_fmu)
    objs = [
        lambda x: simulator.objective(x,INPUT,OUTPUT)
    ]


    n_var = 5
    # Définir le problème
    my_problem= FunctionalProblem(n_var=5,objs = objs,
                            xl=np.array([1e-8, 2e-6,1e-7 , 0.001, 0.85]),
                            xu=np.array([1e-6,1e-3,1e-4 ,0.1,0.98]))
    
    # my_problem = MyProblem()

    # Définir l'algorithme NSGA-II
    algorithm = NSGA2(pop_size=20)
    # algorithm = NSGA2(pop_size=5)
    # algorithm = GA(pop_size=5)

    # Optimiser le problème en utilisant NSGA-II
    result = minimize(my_problem,
                    algorithm,
                    ('n_gen', 50),
                    seed=1,
                    verbose=True)
    # Afficher les résultats
    print("Optimal solutions:")
    print(result.X)
    print("Optimal objectives:")
    print(result.F)

main()