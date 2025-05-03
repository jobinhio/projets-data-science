import numpy as np
import scipy as sp
import scipy.sparse as spsp
import scipy.sparse.linalg as spsplin
import matplotlib.pyplot as plt

import codemesh as MESH



#------------------------------  solution exate avec f = 1 et mu = 1
def solexacte(x):
    e = np.exp(1)
    f = (-np.exp(x) + e*np.sinh(x) - e*np.cosh(x)  + e + 1)/(1 + e)
    return f


#------------------------------- classe EF

class fem:
    def __init__(self, mh):
        self.mh = mh
        self.A_1sp = []
        self.A_2sp = []
        self.Msp = []
        self.b = []
    
    def assemble_matspsp(self,l,k,N,h):
    ## On est sur un intervale identifié par les points [x_l,x_k] 
        diag = []

        for i in range(N):
            diag.append(2*((i > l) and (i < k)) + 1*(i==k or i==l))

        supdiag = np.zeros(N-1)
        infdiag = np.zeros(N-1)

        for i in range(l,k):
            supdiag[i] =-1
            infdiag[i] =-1

        A = spsp.diags([supdiag, diag, infdiag], [1, 0, -1])
        return A/h

    def assemble_A_omega1sp(self):
        N = self.mh.Nel
        h = self.mh.h
        l = self.mh.id_Omega1[0] # 0
        k = self.mh.id_Omega1[1] # 19
        A1sp = self.assemble_matspsp(l,k,N,h)

        l = self.mh.id_Omega1[2] # 21
        k = self.mh.id_Omega1[3] # 39
        A2sp = self.assemble_matspsp(l,k,N,h)

        l = self.mh.id_Omega1[4] # 41
        k = self.mh.id_Omega1[5] # 59
        A3sp = self.assemble_matspsp(l,k,N,h)

        l = self.mh.id_Omega1[6] # 61
        k = self.mh.id_Omega1[7] # 79
        A4sp = self.assemble_matspsp(l,k,N,h)

        l = self.mh.id_Omega1[8] # 81
        k = self.mh.id_Omega1[9] # 100
        A5sp = self.assemble_matspsp(l,k,N,h)
        

        A_1sp = A1sp  + A2sp +A3sp + A4sp + A5sp
       
        # C-L sp

        A_1sp = spsp.lil_matrix(A_1sp) #spsp.csr_matrix(A_1sp)
        A_1sp[0,:] = 0
        A_1sp[0,0] = 1
        A_1sp[-1,:] = 0
        A_1sp[-1,-1] = 1

        self.A_1sp = A_1sp 


    def assemble_A_omega2sp(self):
        N = self.mh.Nel
        h = self.mh.h 
        l = self.mh.id_Omega2[0] # 19
        k = self.mh.id_Omega2[1] # 21
        A1sp = self.assemble_matspsp(l,k,N,h)

        l = self.mh.id_Omega2[2] # 39
        k = self.mh.id_Omega2[3] # 41
        A2sp = self.assemble_matspsp(l,k,N,h)

        l = self.mh.id_Omega2[4] # 59
        k = self.mh.id_Omega2[5] # 61
        A3sp = self.assemble_matspsp(l,k,N,h)

        l = self.mh.id_Omega2[6] # 79
        k = self.mh.id_Omega2[7] # 81
        A4sp = self.assemble_matspsp(l,k,N,h)



        A_2sp = A1sp  + A2sp +A3sp + A4sp 
    
        A_2sp = spsp.lil_matrix(A_2sp) #spsp.csr_matrix(A_2sp)
        # C-L sp

        A_2sp[0,:] = 0
        A_2sp[-1,:] = 0

        self.A_2sp = A_2sp
        
    def assemble_matMspsp(self):
        ## On est sur un intervale identifié par les points [x_l,x_k] 
        diag = []
        N = self.mh.Nel
        h = self.mh.h
        for i in range(N):
            diag.append(2/3)

        supdiag = np.zeros(N-1)
        infdiag = np.zeros(N-1)

        for i in range(N-1):
            supdiag[i] =1/6
            infdiag[i] =1/6

        A = spsp.diags([supdiag, diag, infdiag], [1, 0, -1])
        A = A*h

        A =  spsp.lil_matrix(A)  #spsp.csr_matrix(A)

        # C-L
        A[0,:] = 0
        A[-1,:] = 0

        self.Msp = A
 
    def assemble_matb(self):
        N = self.mh.Nel
        b = np.zeros((N))
        for i in range(N):
            b[i] = self.mh.h
        b[0] = 0
        b[-1] = 0

        self.b = b


    def assemble_matrix(self):
        self.assemble_A_omega1sp()
        self.assemble_A_omega2sp()
        self.assemble_matMspsp()
        self.assemble_matb()

        A_1,A_2,M ,b = self.A_1sp,self.A_2sp,self.Msp,self.b

        return A_1,A_2,M ,b


    def U(self,mu):
        A_1,A_2,M ,b = self.assemble_matrix()
        A = A_1 + mu*A_2 + M

        uef = spsplin.spsolve(A,b)
        
        return uef

    def solve(self, mu, plot=True):
        nodes = self.mh.nodes
        uef = self.U(mu)
        uex = solexacte(nodes)

        if plot:
            plt.plot( nodes,uef, '.',label='$u_{EF}$')
            plt.plot(nodes,uex, label='$u_{ex}$')
            plt.legend(loc='best')
            plt.title("Résolution de l'équation $-u'' + u = 1$ ")
            plt.show()
        
        return uef 


#------------------------------ Etude de convergence 


def genere_norme(Liste_n,mu) :
    # calcul de uapp en fonction de n
    L_normL2 =[]
    L_normeH1 =[]

    for n in Liste_n :
        # Maillage omega
        mh = MESH.mesh(n)
        nodes = mh.nodes


        # Assemblage matrix
        femP1 = fem(mh)
        A_1,A_2,M ,_ = femP1.assemble_matrix()
        N = A_1 + mu*A_2
    

        # calcul de uex  et uef
        uex = solexacte(nodes)
        uef = femP1.U(mu)

        # Norme 
        normL2 = np.sqrt(np.transpose((uex - uef))@ M @(uex - uef))
        L_normL2.append(normL2)
        normeH1 = np.sqrt(np.transpose((uex - uef))@(M + N) @(uex - uef))
        L_normeH1.append(normeH1)

    return L_normL2 , L_normeH1


def plot_norme(H,L_normL2  , L_normeH1):
    plt.loglog(H[:-1],L_normeH1[:-1], 'x-',label ='$H^{1}$')
    plt.loglog(H[:-1],L_normL2[:-1], '.-',label = '$L^{2}$')
    plt.legend(loc='best')
    plt.ylabel('Erreurs')
    plt.xlabel('h')
    plt.title("Erreur en normes $L^{2}$ et $H^{1}$")
    plt.show()

def print_pente(H,L_normL2  , L_normeH1):
    k,l = 2,8
    h1 = H[k]
    h2 = H[l]
    err_1H1 = L_normeH1[k]
    err_2H1 = L_normeH1[l]

    err_1L2 = L_normL2[k]
    err_2L2 = L_normL2[l]

    pente_H1 = np.log(err_1H1/err_2H1)/np.log(h1/h2)
    pente_L2 = np.log(err_1L2/err_2L2)/np.log(h1/h2)
    print('pente H1 = ', pente_H1)
    print('pente L2 = ', pente_L2)

def genere_uapp(Liste_n,mu) :
    # calcul de uapp en fonction de n
    Liste_uapp = []
    Liste_m = []
    for n in Liste_n :
        # Maillage omega
        mh = MESH.mesh(n)
        Liste_m.append(mh.nodes)
  
        # sol EF
        femP1 = fem(mh)
        uapp = femP1.U(mu)
        Liste_uapp.append(uapp)
    return Liste_m ,Liste_uapp

def genere_uappinterp(Liste_m ,Liste_uapp,nodes):
    U_h = []
    for i in range(len(Liste_m)):
        x = Liste_m[i]
        y = Liste_uapp[i]
        yinterp = np.interp(nodes, x, y)
        U_h.append(yinterp)
    return U_h

def norm_P1(uex, U_h,M,N):
    L_normL2 =[]
    L_normeH1 =[]
    for i in range (len(U_h)):
        normL2 = np.sqrt(np.transpose((uex - U_h[i]))@ M @(uex - U_h[i]))
        L_normL2.append(normL2)
        normeH1 = np.sqrt(np.transpose((uex - U_h[i]))@(M + N)@(uex - U_h[i]))
        L_normeH1.append(normeH1)
    return L_normL2 , L_normeH1

def plot_norme(H,L_normL2  , L_normeH1):
    plt.loglog(H[:-1],L_normeH1[:-1], 'x-',label ='H1')
    plt.loglog(H[:-1],L_normL2[:-1], '.-',label = 'L2')
    plt.legend(loc='best')
    plt.title("Erreur en norme L2 et H1")
    plt.show()

def print_pente(H,L_normL2  , L_normeH1):
    k,l = 2,8
    h1 = H[k]
    h2 = H[l]
    err_1H1 = L_normeH1[k]
    err_2H1 = L_normeH1[l]

    err_1L2 = L_normL2[k]
    err_2L2 = L_normL2[l]

    pente_H1 = np.log(err_1H1/err_2H1)/np.log(h1/h2)
    pente_L2 = np.log(err_1L2/err_2L2)/np.log(h1/h2)
    print('pente H1 = ', pente_H1)
    print('pente L2 = ', pente_L2)