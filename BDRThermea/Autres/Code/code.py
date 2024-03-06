# -*- coding: utf-8 -*-
"""
Created on Tue Feb 26 15:05:03 2019
Small script to import the test FMU PAC_0test1.fmu'
@author: BDU Heat Pump
"""

# Import the needed (FMPy) packages
from fmpy import dump, read_model_description, extract
from fmpy.fmi2 import FMU2Slave
from fmpy.util import plot_result #, download_test_file
import numpy as np
#import shutil


def simulate_heat_pump_fmu(show_plot=True):
    fmu_filename = 'HPFMU_20_Linux.fmu'
    start_time = 0.0
    stop_time = 10.0
    step_size = 1.0

    print('Reading the model description...')
    model_description = read_model_description(fmu_filename)

    vr = {variable.name: variable.valueReference for variable in model_description.modelVariables}

    input_variables = [
        var for var in model_description.modelVariables if var.causality == 'input']
    print("Input Variables:")
    for var in input_variables:
        print(f"{var.name} (Reference: {var.valueReference}, Start: {var.start})")


    unzipdir = extract(fmu_filename)

    fmu = FMU2Slave(guid=model_description.guid,
                    unzipDirectory=unzipdir,
                    modelIdentifier=model_description.coSimulation.modelIdentifier,
                    instanceName='instance1')
    fmu.instantiate()

    start_values = {
        'u_compressorFrequency': 88.2,     # Hz
        'u_VFlow': 1.33 / 3600,            # m3/s
        'u_T_watrer_in': 303.15,           # K
        'u_T_air': 285.15,                 # K
        # Ajouter les nouveaux paramètres ici
        'x_areaLeakage': 5e-7,             # m², valeur dans [1e-8 ; 1e-6]
        'x_areaSuctionValve': 5e-4,        # m², valeur dans [2e-6 ; 1e-3]
        'x_areaDischargeValve': 5e-5,      # m², valeur dans [1e-4 ; 1e-7]
        'x_relativeDeadSpace': 0.05,       # valeur dans [0.001 ; 0.1]
        'x_driveEfficiency': 0.9           # valeur dans [0.85 ; 0.98]
    }

    fmu.setupExperiment(startTime=start_time)
    print("Valeurs d'entrée définies pour la simulation :")
    for var_name, start_value in start_values.items():
        print(f"{var_name}: {start_value}")
        fmu.setReal([vr[var_name]], [start_value])

    fmu.enterInitializationMode()
    fmu.exitInitializationMode()

    print('Simulating...')
    time = np.arange(start_time, stop_time, step_size)
    results = []

    for t in time:
        fmu.doStep(currentCommunicationPoint=t,
                   communicationStepSize=step_size)
        results.append({})
    fmu.terminate()
    fmu.freeInstance()

    if show_plot:
        pass

    print('Done Simulating FMU...')
    return results


if __name__ == '__main__':
    simulate_heat_pump_fmu()