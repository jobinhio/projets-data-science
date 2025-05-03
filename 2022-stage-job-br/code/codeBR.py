import codeEF as EF 
import codemesh as MESH


import numpy as np
import matplotlib.pyplot as plt




class Br:
    def __init__(self, femP1,N_mu):
        self.fem = femP1
        self.N_mu = N_mu

        # liste mu et mu test à generer
        self.list_mu_test = dict()
        self.list_mu = dict()

        # representer Abr et Bbr
        self.V0 = []
        self.V1 = []
        self.Bbr = []

        # list greedy
        self.list_greedy = []
        self.list_mu_greedy = []

        # N_0
        self.N_0 = 0


        #genere liste_mu
    def genere_liste_mu(self):
        b =1
        a = 0.01
        Liste_mu = (b - a) *np.random.random_sample((self.N_mu,)) + a
        self.Liste_mu = list(np.unique(np.round(Liste_mu ,3))) 
        Liste_mu = list(np.unique(np.round(Liste_mu ,3))) 

        for i in range(len(Liste_mu)):
            self.list_mu['mu' + str(i)] = Liste_mu[i] 
        
        # N_mu peut changer
        self.N_mu = len(Liste_mu) 

         # on génère la liste des solutions
    def give_liste_mu_test(self):
        liste_mu = self.Liste_mu
        for i in range(len(liste_mu)):
            self.list_mu_test['mu' + str(i)] = self.fem.U(liste_mu[i])
        

        # on calcul V0,V1,Bbr
    def build_red_matrices(self,Ua,Ua_t):
        A1 = (self.fem.A_1sp).toarray()
        A2 = (self.fem.A_2sp).toarray()
        M = (self.fem.Msp).toarray()
        b = self.fem.b

        Bbr = b.dot(Ua_t)
        self.Bbr = Bbr

        V0 = (Ua.dot(A1 + M)).dot(Ua_t)
        V1 = (Ua.dot(A2)).dot(Ua_t)

        self.V0, self.V1, self.Bbr = V0, V1, Bbr

        return V0,V1,Bbr

        # Resolution du pb BR en construisant Abr et Bbr
    def solveRB(self,mu,V0,V1,Bbr,Ua):
        Abr = V0 + mu*V1 
        Xbr = np.linalg.solve(Abr, Bbr)  #np.linalg.lstsq(Abr, Bbr)[0]  
        

        Ubr = 0
        for i in range(len(Xbr)):
            Ubr += Xbr[i]*Ua[i]

        return Ubr



    def normL2(self,V):
        M = (self.fem.Msp).toarray()
        V_t = np.transpose(V)
        norme = (V_t.dot(M)).dot(V)
        return norme



    # assemble list_greedy fct de base u(mui)
    def Greedy(self,N_0):
        self.N_0 = N_0
        list_greedy = [] # va contenir les u(mu_1),...,u(mu_Nmax) 
        Liste_mu_test = self.list_mu_test
        Liste_mu = self.list_mu
        
        mu1 = 0.01 # fixé
        
        # on complete self.list_mu_greedy
        self.list_mu_greedy.append(mu1)

        # on suprimer le premier mu1 de la liste s'il y ait
        if mu1 in Liste_mu :
            Liste_mu.remove(mu1)
        list_greedy.append(self.fem.U(mu1))


        # recuperation de la matrice M pour le calcul de la norme
        M = (self.fem.Msp).toarray()
        L_delta , L_cle = [], []


        mu_garder = []
        err = 0

 
        for i in range(1,N_0):

            Ua = np.stack(list_greedy) # on transorme la liste en matrice par colonnes
            Ua_t = np.transpose(Ua)
            V0, V1,Bbr = self.build_red_matrices(Ua,Ua_t)


            # on garde uniquement les cle_mu et les delta 
            for cle,mu in Liste_mu.items():
                delta = self.normL2(Liste_mu_test[cle] - self.solveRB(mu,V0,V1,Bbr,Ua))
                L_delta.append(delta)
                L_cle.append(cle)

            index_best_mu = np.argmax(np.array(L_delta))
            mu_keys = L_cle[index_best_mu]


            # on complete self.list_mu_greedy
            self.list_mu_greedy.append(Liste_mu[mu_keys])
            
            err = np.max(np.array(L_delta))

            



            # debugage 
            # mu_garder.append(Liste_mu[mu_keys])
            # print('-----------------------------------')
            # print('mu_keys :',mu_keys)
            # print('index_best_mu :' ,index_best_mu)
            # print('L_delta[index_best_mu] :' ,L_delta[index_best_mu])
            # print('err :',err)
            # print('Liste_mu[mu_keys]:',Liste_mu[mu_keys])
            # print('mu_garder:',mu_garder)
            # print('min,max de delta:' ,np.min(L_delta), np.max(L_delta))
            # print(' index de min,max de delta:' ,np.argmin(L_delta), np.argmax(L_delta))



            # mise a zero
            L_delta , L_cle = [], []

       
            # ajout u(mu) dans liste greedy
            list_greedy.append( Liste_mu_test[mu_keys] )

            # suppresion de mu dans Liste_mu pour les prochaines étapes
            del Liste_mu[mu_keys]


            # # vérifier le cond  est correcte
            # cond = np.linalg.cond(np.array(list_greedy))
            # print('cond,err  :',cond,err)

            # if cond > 1e10 :
            #     print('cond,err  :',cond,err)
            #     del list_greedy[-1]
            #     break;

      
        self.list_greedy = list_greedy



        # resultion du pb BR apres construction de Abr et Bbr
    def Ubr(self,mu):
        Bbr , V0, V1 = self.Bbr ,self.V0 ,self.V1
        Abr = V0 + mu*V1 
        Xbr = np.linalg.solve(Abr, Bbr)  #np.linalg.lstsq(Abr, Bbr)[0]  
        
        list_greedy = self.list_greedy
        Ubr = 0
        for i in range(len(Xbr)):
            Ubr += Xbr[i]*list_greedy[i]

        return Ubr
     
  
    # on affiche les 3 sol ex,br,ef
    def solveUbr(self, mu, plot=True):
        nodes = self.fem.mh.nodes
        Ubr = self.Ubr(mu)
        uef = self.fem.U(mu)
        uex = EF.solexacte(nodes)

        if plot:
            plt.plot( nodes,Ubr,'.',label='$u_{BR}$')
            plt.plot( nodes,uef,label='$u_{EF}$')
            #plt.plot(nodes,uex, label='$u_{ex}$')
            plt.legend(loc='best')
            plt.xlabel('noeuds')
            plt.title("Résolution de  $-u'' + u = 1$, avec $N_0$ =  " + str(self.N_0))
            plt.show()
        
        return Ubr


def objet_br(Nel,N_mu):
    # Maillage omega
    Nel = 100
    mh = MESH.mesh(Nel)

    # classe fem
    femP1 = EF.fem(mh)

    #classe BR
    N_mu = 100
    br = Br(femP1,N_mu)

    #genere liste_mu et liste_mu_test
    br.genere_liste_mu()
    br.give_liste_mu_test()

    return br




#---------------------------------- conditionnement

def give_conditionnement(liste_N0):
    # Créer notre classe br 
    Nel,N_mu = 100,100
    br = objet_br(Nel,N_mu)

    L_cond_V0 = []
    L_cond_V1 = []

    for N_0 in liste_N0 :        
        br.Greedy(N_0)
        Ua = np.array(br.list_greedy)
        Ua_t = np.transpose(Ua)
        V0,V1,Bbr =  br.build_red_matrices(Ua,Ua_t)


        cond_V0 = np.linalg.cond(V0)
        cond_V1 = np.linalg.cond(V1)
        L_cond_V0.append(cond_V0)
        L_cond_V1.append(cond_V1)

    return L_cond_V0,L_cond_V1


def plot_conditionnement(L_cond_V0, L_cond_V1,liste_N0 ):
    plt.loglog(liste_N0,L_cond_V0,'-x',label = '$K(V_{0}^{BR})$')
    plt.loglog(liste_N0,L_cond_V1,'-x',label = '$K(V_{1}^{BR})$')


    plt.legend(loc='best')
    plt.xlabel("valeur de " + '$N_0$')
    plt.ylabel("Conditionnement")
    plt.title("Conditionnement de "+ '$V_{0}^{BR}$' " et " + '$V_{1}^{BR}$' + " en fonction de " + '$N_0$')
    plt.show()





#---------------------------------- Qualité Br

def give_lamda_mu_test(M):
    b =1
    a = 0.01
    Liste_mu = (b - a) *np.random.random_sample(M) + a
    Liste_mu = list(np.unique(np.round(Liste_mu ,10))) 
    return Liste_mu


def genere_err(L_M,N_0):
    # Créer notre classe br 
    Nel,N_mu = 100,100
    br = objet_br(Nel,N_mu)
    femP1 = br.fem

    # on applique l'algo glouton
    br.Greedy(N_0)


    L_err =[]
    for M in L_M :
        # genere lambda test
        lamda_mu_test = give_lamda_mu_test(M)
    
        # calcul de l'erreur
        err = np.max([br.normL2(femP1.U(mu) - br.Ubr(mu)) for mu in lamda_mu_test ])
        L_err.append(err)
    
    return L_err

def plot_res(L_M,L_err):
    plt.loglog(L_err ,'x-')
    plt.title("Qualité de la Base Réduite ")
    plt.ylabel('Erreur $\epsilon$')
    plt.xlabel('$log(M)$')
    plt.show()
    print('L_M :',L_M)
    print('L_err :',L_err)





#--------------------------------- Etude d'erreur sur Omega et mu = 0.05 

def sol_ef_br(mu,Nel,N_mu,N_0):
       # Créer notre classe br 
    br = objet_br(Nel,N_mu)
    femP1 = br.fem
    nodes = femP1.mh.nodes
    
    # on applique l'algo glouton 
    br.Greedy(N_0)


    # resolution
    uef = femP1.U(mu)
    ubr = br.Ubr(mu)
    mu_keep = br.list_mu_greedy

    return uef, ubr, mu_keep, nodes


def plotsol_ef_br(uef, ubr, nodes, mu_keep, mu):
    # on affiche la liste mu greedy
    print("$P_{trial}$" + ' :' , mu_keep)

    plt.plot(nodes,uef,label ='sol EF ' )
    plt.plot(nodes,ubr,'.',label = 'sol Br ')
    plt.title("Résolution de l'équation $-D \cdot u'' + u = 1$ , avec $\mu = $" + str(mu))
    plt.legend(loc='best')
    plt.show()

def ploterr_ef_br(uef, ubr, nodes, mu):
    err = np.abs(uef - ubr)
    plt.plot(nodes,err)
    plt.title("Erreur absolue entre les Solutions EF et BR, avec $\mu = $" + str(mu))
    plt.show()
