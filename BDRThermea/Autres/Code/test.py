from fmpy import dump, read_model_description, extract
from fmpy.fmi2 import FMU2Slave
from fmpy.util import plot_result #, download_test_file
import numpy as np

fmu_filename =  'HPFMU_20_Linux.fmu'
dump(fmu_filename)