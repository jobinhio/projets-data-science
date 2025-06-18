from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
import numpy as np
import os
import logging
import threading


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HeatPumpSimulator:
    def __init__(self, fmu_filename, start_time=0.0, stop_time=1500.0, step_size=1.0):
        """
        Initialise le simulateur de pompe à chaleur.

        fmu_filename: nom du fichier FMU
        start_time: temps de début de la simulation
        stop_time: temps de fin de la simulation
        step_size: pas de temps de la simulation
        """
        self.fmu_filename = fmu_filename
        self.start_time = start_time
        self.stop_time = stop_time
        self.step_size = step_size
        self.model_description = read_model_description(fmu_filename)
        self.vr = {
            variable.name: variable.valueReference for variable in self.model_description.modelVariables}
        self.unzip_directory = self.prepare_fmu()

    def prepare_fmu(self):
        """Prépare le FMU pour la simulation."""
        notebook_dir = os.path.dirname(os.path.abspath("__file__"))

        fmu_absolute_path = os.path.join(notebook_dir, self.fmu_filename)

        fmu_directory = os.path.dirname(fmu_absolute_path)
        unzip_directory = os.path.join(fmu_directory, 'unzip')
        os.makedirs(unzip_directory, exist_ok=True)
        extract(fmu_absolute_path, unzipdir=unzip_directory)

        return unzip_directory

    # Dictionnaire des paramètres avec leurs valeurs min et max
    PARAM_RANGES = {
        'x_areaLeakage': (1e-8, 1e-6),
        'x_areaSuctionValve': (2e-6, 1e-3),
        'x_areaDischargeValve': (1e-7, 1e-4),
        'x_relativeDeadSpace': (0.001, 0.1),
        'x_driveEfficiency': (0.85, 0.98)
    }

    def verify_parameter_ranges(self, start_values):
        """
        Vérifie que les valeurs des paramètres sont dans les bornes.

        start_values: dictionnaire des paramètres avec leurs valeurs
        """

        for param, value in start_values.items():
            if param in self.PARAM_RANGES:
                min_val, max_val = self.PARAM_RANGES[param]
                if not min_val <= value <= max_val:
                    raise ValueError(
                        f"Value of {param} ({value}) is out of range [{min_val}, {max_val}]")

    def simulate_with_timeout(self, start_values, timeout=10):
        """
        Exécute une simulation avec un timeout.

        start_values: dictionnaire des paramètres avec leurs valeurs
        timeout: temps en secondes avant d'arrêter la simulation
        """

        results_container = {"results": None}

        def _simulate():
            """Fonction interne pour exécuter la simulation."""
            results_container["results"] = self.simulate(start_values)

        # Création d'un thread pour exécuter la simulation
        simulation_thread = threading.Thread(target=_simulate)
        simulation_thread.start()
        # Attente de la fin de la simulation ou du timeout
        simulation_thread.join(timeout)

        if simulation_thread.is_alive():
            # Si le thread est toujours vivant après le timeout, la simulation est arrêtée
            print(f"Simulation timeout reached for parameters: {start_values}")
            return {}  # Retourne un dictionnaire vide en cas de timeout

        return results_container["results"]

    def simulate(self, start_values, show_plot=False):
        """
        Exécute une simulation.

        start_values: dictionnaire des paramètres avec leurs valeurs
        show_plot: affiche le graphe des résultats si True
        """
        try:
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
            return {}

    def setup_simulation(self, fmu, start_values):
        """
        Initialise la simulation.

        fmu: FMU2Slave
        start_values: dictionnaire des paramètres avec leurs valeurs

        """
        fmu.setupExperiment(startTime=self.start_time)
        for var_name, start_value in start_values.items():
            fmu.setReal([self.vr[var_name]], [start_value])
        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

    def run_simulation(self, fmu):
        """
        Exécute la simulation.

        fmu: FMU2Slave
        """

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

    def plot_results(self, results):
        pass
