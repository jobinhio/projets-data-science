from deap import base, creator, tools, algorithms
import time
from simulation_class import HeatPumpSimulator
from scipy.optimize import minimize
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
import numpy as np
import pandas as pd
import os
import random
from deap import base, creator, tools, algorithms
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        try:
            print("Début de la simulation avec les paramètres :", start_values)
            fmu = FMU2Slave(guid=self.model_description.guid,
                            modelIdentifier=self.model_description.coSimulation.modelIdentifier,
                            unzipDirectory=self.unzip_directory)
            self.verify_parameter_ranges(start_values)
            try:
                fmu.instantiate()
                self.setup_simulation(fmu, start_values)
                results = self.run_simulation(fmu)
                if show_plot:
                    self.plot_results(results)
            finally:
                fmu.terminate()
                fmu.freeInstance()
            return results
        except Exception as e:
            print(f"Erreur durant la simulation : {e}")
            return {}   # Retourne un DataFrame vide en cas d'erreur

    def setup_simulation(self, fmu, start_values):
        fmu.setupExperiment(startTime=self.start_time)
        for var_name, start_value in start_values.items():
            fmu.setReal([self.vr[var_name]], [start_value])
        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

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
            # print(f"Temps de simulation : {t}, Résultats : {output_values}")

        return results

    def plot_results(self, results):
        pass


df_input = pd.read_csv(
    '/home/u4/csmi/2022/barkan/BDR/2023-m2-bdrthermea/multi-physics-modeling/data/df_input.csv', sep=',')

df_output = pd.read_csv(
    '/home/u4/csmi/2022/barkan/BDR/2023-m2-bdrthermea/multi-physics-modeling/data/df_output.csv', sep=',')

df_input_no_defrost = df_input[df_input['Defrosts'] == "no"]
df_output_no_defrost = df_output[df_output['Defrosts'] == "no"]

# train 90% test 10%
df_input_no_defrost_train = df_input_no_defrost.sample(
    frac=0.9, random_state=0)
df_output_no_defrost_train = df_output_no_defrost.sample(
    frac=0.9, random_state=0)
df_input_no_defrost_test = df_input_no_defrost.drop(
    df_input_no_defrost_train.index)
df_output_no_defrost_test = df_output_no_defrost.drop(
    df_output_no_defrost_train.index)


# # print le max des frequences
# print(df_input_no_defrost['Frequency'].max())
# print(df_input_no_defrost['Frequency'].min())


# Initialisation du simulateur
simulator = HeatPumpSimulator(
    '/home/u4/csmi/2022/barkan/BDR/2023-m2-bdrthermea/multi-physics-modeling/FMU/HPFMU_20_Linux.fmu')


# def drive_efficiency(freq, coeffs):
#     eff = sum(c * freq ** i for i, c in enumerate(coeffs[::-1]))
#     if not np.isfinite(eff):
#         return 0.85  # Retournez une valeur par défaut si le calcul donne nan ou inf
#     return min(max(eff, 0.85), 0.98)

# Fonction objectif pour l'optimisation


# garder les deux premières lignes
df_input_no_defrost_train = df_input_no_defrost_train.iloc[0:10]
df_output_no_defrost_train = df_output_no_defrost_train.iloc[0:10]


def force_within_bounds(value, min_val, max_val):
    return max(min_val, min(max_val, value))


def objective_function(params):
    print("\nÉvaluation des paramètres :", params)
    areaLeakage, areaSuctionValve, areaDischargeValve, relativeDeadSpace, x_driveEfficiency = params

    # Forcer les paramètres à rester dans leur intervalle
    areaLeakage = force_within_bounds(areaLeakage, 1e-8, 1e-6)
    areaSuctionValve = force_within_bounds(areaSuctionValve, 2e-6, 1e-3)
    areaDischargeValve = force_within_bounds(areaDischargeValve, 1e-7, 1e-4)
    relativeDeadSpace = force_within_bounds(relativeDeadSpace, 0.001, 0.1)
    x_driveEfficiency = force_within_bounds(x_driveEfficiency, 0.85, 0.98)
    total_error = 0

    for index, (input_row, output_row) in enumerate(zip(df_input_no_defrost_train.itertuples(), df_output_no_defrost_train.itertuples())):
        print(
            f"\nTraitement de la ligne {index + 1} / {len(df_input_no_defrost_train)}")

        start_values = {
            'u_compressorFrequency': input_row.Frequency,
            'u_VFlow': input_row.Flow,
            'u_T_watrer_in': input_row.Water_in,
            'u_T_air': input_row.T_air,
            'x_areaLeakage': areaLeakage,
            'x_areaSuctionValve': areaSuctionValve,
            'x_areaDischargeValve': areaDischargeValve,
            'x_relativeDeadSpace': relativeDeadSpace,
            'x_driveEfficiency': x_driveEfficiency
        }

        simulation_result = simulator.simulate(start_values)
        if not simulation_result:  # Vérifie si le dictionnaire est vide
            print("La simulation a échoué, aucun résultat à analyser.")
            return (float('inf'),)  # Retourner une grande valeur d'erreur
        last_row = pd.DataFrame(simulation_result).iloc[-1]

        error = np.sum((last_row[['y_T_out', 'y_heatPower', 'y_elecPower', 'y_COP']] -
                        [output_row.y_T_out, output_row.y_heatPower, output_row.y_elecPower, output_row.y_COP]) ** 2)
        total_error += error
        print(f"Erreur pour la ligne {index + 1} : {error}")
        print(
            f"Traitement de la ligne {index + 1} / {len(df_input_no_defrost_train)}")

    print(f"Erreur totale pour ces paramètres : {total_error}")
    return (total_error,)


# Objectif de minimisation
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()

# Générateurs pour chaque paramètre
toolbox.register("attr_areaLeakage", random.uniform, 1e-8, 1e-6)
toolbox.register("attr_areaSuctionValve", random.uniform, 2e-6, 1e-3)
toolbox.register("attr_areaDischargeValve", random.uniform, 1e-7, 1e-4)
toolbox.register("attr_relativeDeadSpace", random.uniform, 0.001, 0.1)
toolbox.register("attr_x_driveEfficiency", random.uniform, 0.85, 0.98)

# Structure d'un individu
toolbox.register("individual", tools.initCycle, creator.Individual,
                 (toolbox.attr_areaLeakage, toolbox.attr_areaSuctionValve, toolbox.attr_areaDischargeValve,
                  toolbox.attr_relativeDeadSpace, toolbox.attr_x_driveEfficiency), n=1)

toolbox.register("population", tools.initRepeat, list, toolbox.individual)

toolbox.register("evaluate", objective_function)
toolbox.register("mate", tools.cxTwoPoint)
toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.1)
toolbox.register("select", tools.selNSGA2)


def main():
    population = toolbox.population(n=50)
    ngen = 50

    print("Début de l'optimisation NSGA-II")
    for gen in range(ngen):
        print(f"\nGénération {gen + 1}/{ngen}")
        offspring = algorithms.varAnd(population, toolbox, cxpb=0.7, mutpb=0.2)
        fits = toolbox.map(toolbox.evaluate, offspring)
        for fit, ind in zip(fits, offspring):
            ind.fitness.values = fit
            print(f"Individu : {ind}, Fitness : {fit}")

        population = toolbox.select(offspring, k=len(population))

    print("\nSélection des meilleurs individus")
    best_individuals = tools.selBest(population, k=3)
    for ind in best_individuals:
        print(ind, ind.fitness.values)


main()
