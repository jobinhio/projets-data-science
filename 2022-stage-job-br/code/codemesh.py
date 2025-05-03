import numpy as np
import scipy as sp
import scipy.sparse as spsp
import scipy.sparse.linalg as spsplin
import matplotlib.pyplot as plt
from scipy import interpolate



class mesh:
    def __init__(self,N):        
        self.Nel  =  N - 1 #N 
        self.h = 1/self.Nel
        m = np.arange(0,1,self.h)
        if (len(m) == N ):
                # pas d'ajout de 1 
            self.nodes = m
            self.Nel = np.size(m)
        else :
            self.nodes = np.array(list(m) + [1]) #ajout de 1 
            self.Nel = np.size(self.nodes)


        self.id_Omega1 = []
        self.id_Omega2 = []
        self.id_val_spe = []

        val_spe = [ 0.,0.19, 0.21,0.39,0.41,0.59,0.61,0.79,0.81,1.] 
        self.id_val_spe  = []
        for x in val_spe :
            id = self.identify_nodes(self.nodes,x) 
            self.id_val_spe.append(id)
        self.id_Omega2 = self.id_val_spe [1:-1]
        self.id_Omega1 = self.id_val_spe 
        
        self.nodes = np.array(self.nodes)

    def identify_nodes(self,mesh,a) :
        return np.argmin((np.abs(a-mesh)))