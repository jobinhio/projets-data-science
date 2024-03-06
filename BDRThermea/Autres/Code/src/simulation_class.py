from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
import numpy as np
import pandas as pd
import os

from deap import base, creator, tools, algorithms


import time
from timeout_decorator import timeout, TimeoutError


from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.problems.functional import FunctionalProblem



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

    def simulate(self, start_values, show_plot=False):
        fmu = FMU2Slave(guid=self.model_description.guid,
                        modelIdentifier=self.model_description.coSimulation.modelIdentifier,
                        unzipDirectory=self.unzip_directory)
        self.verify_parameter_ranges(start_values)
        stop_time = 15 #180 #15

        try:
            # Utiliser @timeout uniquement pour la fonction run_simulation(fmu)
            fmu.instantiate()
            self.setup_simulation(fmu, start_values)
            results = self.run_simulation(fmu)
        except TimeoutError:
            print(f"Le temps d'exécution dépasse {stop_time} secondes.\n")
            results = {}

        except Exception as e:
            print(f"Une autre error a été détectée : {type(e).__name__}")
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

    # The simulation takes a maximum of 15 seconds
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
    
    def error_criterion(self,start_values, finish_values):

        results = self.simulate(start_values)

        # If the simulation fails, then the error takes 
        # a large value (infinite) 
        error = 100000

        # Else we calculate the error
        if bool(results):
            Fmu_COP = results['y_COP'] [-1]
            True_COP = finish_values['y_COP']

            Fmu_heatPower = results['y_heatPower'] [-1]
            True_heatPower = finish_values['y_heatPower']

            Fmu_elecPower = results['y_elecPower'] [-1]
            True_elecPower = finish_values['y_elecPower']

            error = abs(True_COP-Fmu_COP) + abs(True_heatPower-Fmu_heatPower) + abs(True_elecPower-Fmu_elecPower)
            print("error absolue :",error)

        return error

    def objective(self,x,start_values,finish_values):
        # We retrieve the parameters of the FMU
        start_values['x_areaLeakage'] = x[0] 
        start_values['x_areaSuctionValve'] = x[1] 
        start_values['x_areaDischargeValve'] = x[2] 
        start_values['x_relativeDeadSpace'] = x[3] 
        start_values['x_driveEfficiency'] = x[4]
        error = self.error_criterion(start_values, finish_values)
        return error 
    
    def apply_NSGA2(self,INPUT,OUTPUT):

        # For each row of the training data, we apply NSGA-II
        n_train = len(INPUT['u_T_watrer_in'])
        n_train = 4
        for i in range(n_train):
            print("i_train  =",i)
            # We input the training input_train and output_train
            start_values = {
                'u_compressorFrequency': INPUT['u_compressorFrequency'].iloc[i],
                'u_VFlow': INPUT['u_VFlow'].iloc[i],
                'u_T_watrer_in': INPUT['u_T_watrer_in'].iloc[i],
                'u_T_air': INPUT['u_T_air'].iloc[i]
            }
            finish_values = {
                'Water_out' : OUTPUT['Water_out'].iloc[i],
                'y_heatPower': OUTPUT['y_heatPower'].iloc[i],  
                'y_elecPower': OUTPUT['y_elecPower'].iloc[i],
                'y_COP': OUTPUT['y_COP'].iloc[i]
            }
            

            # Define the objective function 
            objs = [lambda x: self.objective(x,start_values,finish_values)]

            # Define the problem
            my_problem= FunctionalProblem(n_var=5,objs = objs,
                                    xl=np.array([1e-8, 2e-6,1e-7 , 0.001, 0.85]),
                                    xu=np.array([1e-6,1e-3,1e-4 ,0.1,0.98]))
            
            # Optimize the problem using NSGA-II
            algorithm = NSGA2(pop_size=20)
            result = minimize(my_problem,
                            algorithm,
                            ('n_gen', 50),
                            seed=1,
                            verbose=True)
            # Display the results
            print("Optimal solutions:")
            print(result.X)
            print("Optimal objectives:")
            print(result.F)
        return 0









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



def main():
    # Définir la fonction objectif 
    chemin_fmu = '/home/congo/BDRThermea/2023-m2-bdrthermea/multi-physics-modeling/FMU/HPFMU_20_Linux.fmu'
    simulator = HeatPumpSimulator(chemin_fmu)
    simulator.apply_NSGA2(INPUT,OUTPUT)


main()