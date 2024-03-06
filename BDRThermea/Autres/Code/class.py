from pymoo.core.problem import ElementwiseProblem
from pymoo.optimize import minimize
from pymoo.factory import get_sampling, get_crossover, get_mutation
from pymoo.algorithms.moo.nsga2 import NSGA2
import numpy as np
import pandas as pd
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
from fmpy.util import plot_result


class CustomSimulator:
    def __init__(self, fmu_path):
        self.fmu_path = fmu_path
        self.model_description = read_model_description(fmu_path)
        self.unzipdir = extract(fmu_path)
        self.modelIdentifier = self.model_description.coSimulation.modelIdentifier
        self.guid = self.model_description.guid
        self.vrs = {
            var.name: var.valueReference for var in self.model_description.modelVariables}

    def simulate(self, time, frequency, tair, twater, Qwater, show_plot=False):
        start_time = 0.0
        stop_time = 600
        step_size = 1

        fmu = FMU2Slave(guid=self.guid, unzipDirectory=self.unzipdir,
                        modelIdentifier=self.modelIdentifier, instanceName='instance1')

        fmu.instantiate()
        fmu.setupExperiment(startTime=start_time)
        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

        # Set initial values based on the parameters
        fmu.setReal([self.vrs['Frequency']], [frequency])
        fmu.setReal([self.vrs['Temperature_cold_source']], [tair])
        # Add other parameters as needed

        time = start_time
        rows = []

        while time < stop_time:
            # Update the inputs at each step if necessary
            fmu.setReal([self.vrs['Frequency']], [frequency])
            fmu.setReal([self.vrs['Temperature_cold_source']], [tair])

            fmu.doStep(currentCommunicationPoint=time,
                       communicationStepSize=step_size)
            # Retrieve the outputs
            Comp_Freq, Air_Ext_T, HP_Heat = fmu.getReal(
                [self.vrs['Frequency'], self.vrs['Temperature_cold_source'], self.vrs['Power']])
            rows.append((time, Comp_Freq, Air_Ext_T, HP_Heat))
            time += step_size

        fmu.terminate()
        fmu.freeInstance()

        result = np.array(rows, dtype=np.dtype([('time', np.float64), (
            'Comp_Frequency', np.float64), ('Air_Ext_T', np.float64), ('HP_Heat', np.float64)]))

        if show_plot:
            plot_result(result)

    def run_simulations(self, dataframe):
        for index, row in dataframe.iterrows():
            self.simulate(time=row['time'], frequency=row['frequency'],
                          tair=row['tair'], twater=row['twater'], Qwater=row['Qwater'])


class CompressorOptimizationProblem(ElementwiseProblem):
    def __init__(self, lower_bounds, upper_bounds):
        super().__init__(n_var=len(lower_bounds),
                         n_obj=2,  # Nombre d'objectifs
                         xl=np.array(lower_bounds),
                         xu=np.array(upper_bounds))

    def _evaluate(self, x, out, *args, **kwargs):
        objective1, objective2 = evaluate_model(x)
        out["F"] = [objective1, objective2]


# Définir les limites inférieures et supérieures pour les paramètres
lower_bounds = [0.1, 0.1, ...]  # Exemple
upper_bounds = [5.0, 5.0, ...]  # Exemple

problem = CompressorOptimizationProblem(lower_bounds, upper_bounds)

algorithm = NSGA2(
    pop_size=100,
    n_offsprings=10,
    sampling=get_sampling("real_random"),
    crossover=get_crossover("real_sbx", prob=0.9, eta=15),
    mutation=get_mutation("real_pm", eta=20),
    eliminate_duplicates=True
)

res = minimize(problem,
               algorithm,
               ('n_gen', 40),
               verbose=True)

# Analyser les solutions
print("Solutions sur le front de Pareto :")
for solution in res.F:
    print(solution)
