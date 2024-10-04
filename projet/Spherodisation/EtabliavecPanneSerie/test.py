import sys
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
import plotly.graph_objects as go
import plotly.io as pio

class PlotManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plotly avec PyQt5")
        self.setGeometry(100, 100, 1200, 600)

        # Layout principal
        layout = QVBoxLayout(self)
        
        # Créer les graphiques
        self.fig_Mg, self.scatter_Mg = self.create_plot("Consommation de Mg", "Temps", "Mg")
        self.fig_PFC, self.scatter_PFC = self.create_plot("Consommation de Fonte", "Temps", "Fonte")

        # Ajouter les graphiques à la fenêtre PyQt5
        self.web_view_Mg = self.create_web_view(self.fig_Mg)
        self.web_view_PFC = self.create_web_view(self.fig_PFC)
        
        layout.addWidget(self.web_view_Mg)
        layout.addWidget(self.web_view_PFC)

    def create_plot(self, title, xaxis_title, yaxis_title):
        fig = go.Figure()
        scatter = fig.add_scatter(mode='lines+markers').data[0]
        fig.update_layout(title=title, xaxis_title=xaxis_title, yaxis_title=yaxis_title)
        return fig, scatter

    def create_web_view(self, fig):
        # Convertir la figure en HTML
        html = pio.to_html(fig, full_html=False)
        web_view = QWebEngineView()
        web_view.setHtml(html)
        return web_view

    def update_web_view(self, web_view, fig):
        html = pio.to_html(fig, full_html=False)
        web_view.setHtml(html)

    def update_plot_data(self, fig, scatter, xdata, ydata, web_view):
        scatter.update(x=xdata, y=ydata)
        self.update_web_view(web_view, fig)

    def add_colored_segment(self, fig, x0, x1, y0, y1, color, web_view):
        segment = go.Scatter(x=[x0, x1], y=[y0, y1], mode='lines+markers', line=dict(color=color), showlegend=False)
        fig.add_trace(segment)
        self.update_web_view(web_view, fig)

    def determine_segment_color(self, Mg, PFC, Mgmin, PFCmax, PPT):
        if (PFC + PPT) >= PFCmax and Mg <= Mgmin:
            return 'red'
        elif (PFC + PPT) <= PFCmax and Mg <= Mgmin:
            return 'orange'
        else:
            return 'green'

    def update_figure(self, Mg, PFC, timedata, Mgdata, PFCdata, Mgmin, PFCmax, PPT):
        self.update_plot_data(self.fig_PFC, self.scatter_PFC, timedata, PFCdata, self.web_view_PFC)
        if len(timedata) >= 2:
            x0, x1 = timedata[-2], timedata[-1]
            y0, y1 = Mgdata[-2], Mgdata[-1]
            color = self.determine_segment_color(Mg, PFC, Mgmin, PFCmax, PPT)
            self.add_colored_segment(self.fig_Mg, x0, x1, y0, y1, color, self.web_view_Mg)


###--------------------

import os
import pandas as pd

class FileManager:
    def __init__(self, param_file, button_file, disa_file):
        self.param_file = param_file
        self.button_file = button_file
        self.disa_file = disa_file
        self.last_modified_button = None
        self.last_modified_disa = None

        self.running = False
        self.Panne = False
        self.reset = False
        self.DemandePoche = False
        self.AjoutPoche = False
        self.etat_courant = "etat_Consom"

        self.BoutonsEtParamètres = {}
        self.ProgrammeDISA = {}
        self.parametres_generaux = {}


    def read_parametres_generaux(self):
        """Lit le fichier ParamètresGénéraux et retourne un dictionnaire avec les noms de variables et leurs valeurs."""
        try:
            with open(self.param_file, 'r', encoding='utf-8') as file:
                lines = file.read().strip().split('\n')
                variable_names = lines[0].split(';')
                variable_values = lines[1].split(';')
                self.parametres_generaux = {var: float(val.replace(',', '.')) for var, val in zip(variable_names, variable_values)}
        except FileNotFoundError:
            print(f"Le fichier {self.param_file} n'existe pas.")
        except Exception as e:
            print(f"Une erreur est survenue : {e}")

    def read_file_boutons_et_parametres(self):
        """Lit le fichier BoutonsEtParamètres et retourne un dictionnaire avec les valeurs."""
        try:
            with open(self.button_file, 'r', encoding='utf-8') as file:
                content = file.read().strip()
                lines = content.split('\n')
                
                boutons_line = lines[0].split(';')
                self.BoutonsEtParamètres['Boutons'] = boutons_line[1] if boutons_line[0] == "Boutons" else 'STOP'

                second_line_headers = lines[1].split(';')
                third_line_values = lines[2].split(';')
                
                # Utilisation de valeurs par défaut en cas d'absence de données
                self.BoutonsEtParamètres['PPT'] = float(third_line_values[0].replace(',', '.')) if second_line_headers[0] == "PPT" else 0.0
                self.BoutonsEtParamètres['TPT'] = float(third_line_values[1].replace(',', '.')) if second_line_headers[1] == "TPT" else 0.0
                self.BoutonsEtParamètres['S'] = float(third_line_values[2].replace(',', '.')) if second_line_headers[2] == "S" else 0.0
            return self.BoutonsEtParamètres
        except FileNotFoundError:
            print(f"Le fichier {self.button_file} n'existe pas.")
            return None
        except Exception as e:
            print(f"Une erreur est survenue : {e}")
            return None

    def read_programme_disa(self):
        """Lit le fichier ProgrammeDISA et retourne son contenu sous forme de dictionnaire."""
        try:
            df = pd.read_csv(self.disa_file, sep=';', encoding='utf-8', usecols=["Cadences", "Nb Moules", "Poids"])
            self.ProgrammeDISA = df.to_dict(orient='list')
  
        except FileNotFoundError:
            print(f"Le fichier {self.disa_file} n'existe pas.")
        except pd.errors.EmptyDataError:
            print("Le fichier ProgrammeDISA est vide.")
        except Exception as e:
            print(f"Une erreur est survenue : {e}")

    def check_for_updates(self):
        """Vérifie les mises à jour des fichiers et traite les changements si nécessaire."""
        if os.path.exists(self.button_file):
            current_button_mod_time = os.path.getmtime(self.button_file)
            if self.last_modified_button is None or current_button_mod_time > self.last_modified_button:
                self.last_modified_button = current_button_mod_time
                self.handle_buttons(self.read_file_boutons_et_parametres())

        if os.path.exists(self.disa_file):
            current_disa_mod_time = os.path.getmtime(self.disa_file)
            if self.last_modified_disa is None or current_disa_mod_time > self.last_modified_disa:
                self.last_modified_disa = current_disa_mod_time
                self.read_programme_disa()

    def handle_buttons(self, current_BoutonsEtParamètres):
        """Gère les changements d'état en fonction des boutons."""    
        print(f"Fichier BoutonsEtParamètres mis à jour : {current_BoutonsEtParamètres}")
        
        bouton = current_BoutonsEtParamètres['Boutons']
        
        if bouton == "START":
            self.running = True
            self.Panne = False
            self.etat_courant = "etat_Consom"
        
        elif bouton == "STOP":
            self.running = False
        
        elif bouton == "RESET":
            self.reset = True
        
        elif bouton == "DEMANDEPOCHE":
            self.DemandePoche = True

        elif bouton == "AJOUTPOCHE":
            self.AjoutPoche = True

        elif bouton == "SERIE":
            self.etat_courant = "etat_Serie"          

        elif bouton == "PANNE":
            self.Panne = True
            self.etat_courant = "etat_Panne"

        elif bouton == "FIN":
            self.etat_courant = "etat_Fin"




####--------------------

# Pour calculer la longueur du fil fourré 
def calcul_quantite_mg(P,S,t,e,T,R,Mg,K) :
    """
    Calcule la Quantité d'alliage au magnésium (en Kg) à introduire dans la fonte pour obtenir du graphite spherodial.
    Args:
    P: Poids de fonte à traiter en Kg.
    S: Taux de souffre de la fonte de base en %.
    t: Temps de séjour en minutes prévu pour la fonte après traitement.
    T: Température (degrés Celsius) de la fonte au moment du traitement, mesurée au couple.
    R: Rendement en magnésium de l'opération en %.
    Mg: Taux en magnésium dans l'alliage en %.
    K: Quantité de magnésium résiduel nécessaire pour que le graphite soit sous forme sphéroïdal en %.

    Returns:
    Q: Quantité d'alliage au magnésium à utiliser en Kg.
    """
    Q = P * (0.76 * (S - 0.01) + K + t * e) * (T / 1450) ** 2 / (R * Mg / 100)

    return Q

def calcul_longueur_fil( PPT, S, temps_gs, TPT,
    R, masse_fil, masse_mg_fil, Mgmax, eP, 
    PFClimite, Mglimite ):

    # % de Mg à ajouter dans la poche de traitement pour obtenir le Mg maximal
    K = ( Mgmax*(PFClimite + PPT) - Mglimite*PFClimite )/ PPT

    # Masse de Mg à ajouter dans la poche de traitement pour obtenir le Mg maximal
    Mgfil = masse_mg_fil/masse_fil *100
    Q = calcul_quantite_mg(PPT,S,temps_gs,eP,TPT,R,Mgfil,K) # en Kg


    # Longueur de fil pour avoir la masse de Mg manquante
    L = Q / (masse_fil* 1e-3)   # en m

    return K, L



# Calcule du temps limite avant lancement prochain traitement
def calculer_temps_epuis_PFC(PFC, PFCmin, temps_serie, liste_masses_grappes_moules, liste_cadences_moule_par_heure, liste_quantites_moules_a_produire):
    # Calcul de la fonte four consommable
    PFCconsommable = PFC - PFCmin

    # Initialisation du temps total
    temps_total = 0

    # Boucle sur chaque modèle de moules
    for i in range(len(liste_masses_grappes_moules)):
        masse_grappe_i = liste_masses_grappes_moules[i]
        cadence_moule_par_heure_i = liste_cadences_moule_par_heure[i]
        quantite_moules_a_produire_i = liste_quantites_moules_a_produire[i]

        # Calcul de la cadence de fonte en kg/min pour le modèle i
        cadence_fonte_i = (cadence_moule_par_heure_i / 60) * masse_grappe_i  # en kg/min
        
        # Fonte nécessaire pour produire tous les moules de ce modèle
        fonte_necessaire_i = quantite_moules_a_produire_i * masse_grappe_i

        if PFCconsommable >= fonte_necessaire_i:
            # Si la fonte est suffisante pour produire tous les moules
            temps_pour_produire_i = fonte_necessaire_i / cadence_fonte_i
            temps_total += temps_pour_produire_i
            PFCconsommable -= fonte_necessaire_i

            # Ajouter le temps de la série s'il y a d'autres modèles à produire
            if i < len(liste_masses_grappes_moules) - 1:
                temps_total += temps_serie
        else:
            # Si la fonte n'est pas suffisante, calcul du temps possible avec la fonte restante
            temps_possible = PFCconsommable / cadence_fonte_i
            temps_total += temps_possible
            break  # On arrête la boucle, car il n'y a plus de fonte

    return temps_total

def calcul_temps_limite(PFC, Mg, PFCmin, Mgmin, eC, temps_traitement, temps_serie, liste_masses_grappes_moules, liste_cadences_moule_par_heure, liste_quantites_moules_a_produire):
    
    # Temps en minute admissible avant l'ajout dans le four de coulée
    # avant d'atteindre la fonte minimal (en Kg) dans le four de coulée
    temps_epuis_PFC = calculer_temps_epuis_PFC(PFC, PFCmin, temps_serie, liste_masses_grappes_moules, liste_cadences_moule_par_heure, liste_quantites_moules_a_produire)
    delai_avt_traitement_fonte_four = temps_epuis_PFC - temps_traitement


    
    # Temps en minute admissible avant l'ajout dans le four de coulée
    # avant d'atteindre le pourcentage minimal (%) dans le four de coulée
    Mgconsommable = Mg - Mgmin
    temps_epuis_Mg = Mgconsommable/eC
    delai_avt_traitement_mg_four = temps_epuis_Mg - temps_traitement


    # Temps en minute avant de lancer le traitement (Du four de fusion au four de coulée)
    delai_avt_traitement = min(delai_avt_traitement_fonte_four, delai_avt_traitement_mg_four)
    tempslimite = temps_traitement + delai_avt_traitement
    # mise a jour de la masse mg avant ajout poche après consomation de mg
    Mgconsommer = tempslimite*eC
    Mgconsommer = (temps_traitement + delai_avt_traitement)*eC
    Mglimite = Mg - Mgconsommer



    # Mise à jour de la masse de fonte avant ajout dans le four après consommation pendant
    # temps_traitement + delai_avt_traitement
    PFCconsommer = 0
    for i in range(len(liste_masses_grappes_moules)):
        masse_grappe_i = liste_masses_grappes_moules[i]
        cadence_moule_par_heure_i = liste_cadences_moule_par_heure[i]
        quantite_moules_a_produire_i = liste_quantites_moules_a_produire[i]

        # Calcul de la cadence de fonte en kg/min pour le modèle i
        cadence_fonte_i = (cadence_moule_par_heure_i / 60) * masse_grappe_i  # en kg/min

        # Vérification du temps restant par rapport au temps nécessaire pour produire tous les moules de ce modèle
        temps_pour_produire_i = quantite_moules_a_produire_i / (cadence_fonte_i / masse_grappe_i)
        
        if tempslimite > temps_pour_produire_i:
            # Si le délai est supérieur au temps nécessaire, consommer toute la fonte pour ce modèle
            PFCconsommer += cadence_fonte_i * temps_pour_produire_i
            tempslimite -= temps_pour_produire_i

            if i < len(liste_masses_grappes_moules) - 1:
                tempslimite -= temps_serie
        else:
            # Sinon, consommer la fonte en fonction du temps restant
            PFCconsommer += cadence_fonte_i * tempslimite
            break

    PFClimite =  PFC - PFCconsommer


    return delai_avt_traitement, Mglimite, PFClimite


###---------------------



import sys
import time
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer

class Simulation(QWidget):
    def __init__(self, param_file, button_file, disa_file):
        super().__init__()

        # FileManager s'occupe de la lecture et de la gestion des fichiers
        self.file_manager = FileManager(param_file, button_file, disa_file)

        # Initialisation du gestionnaire de plots avec PyQt5 intégré
        self.plot_manager = PlotManager()

        # Variables de simulation
        self.Mg = 0.045  # Quantité initiale de magnésium
        self.PFC = 3500  # Poids de fonte coulée initial
        self.t = 0  # Temps de simulation
        self.timedata = []
        self.Mgdata = []
        self.PFCdata = []

        # Layout pour afficher les graphiques dans PyQt5
        layout = QVBoxLayout(self)
        layout.addWidget(self.plot_manager)

        # Timer pour gérer les étapes de simulation dans une boucle d'événements
        self.timer = QTimer()
        self.timer.timeout.connect(self.step)

    def initialize_simulation(self):
        """Initialise la simulation en lisant les fichiers nécessaires via FileManager."""
        self.file_manager.read_parametres_generaux()
        self.file_manager.read_programme_disa()
        self.file_manager.read_file_boutons_et_parametres()

        if self.file_manager.parametres_generaux and self.file_manager.ProgrammeDISA and self.file_manager.BoutonsEtParamètres:
            print("Simulation initialisée avec succès.")
        else:
            print("Échec de l'initialisation de la simulation. Vérifiez les fichiers.")

    def step(self):
        """Effectue une étape de la simulation."""
        if self.t != 0:
            self.file_manager.etat_courant = self.handle_state(self.file_manager.etat_courant)
            self.handle_poche()
            self.record_data()
            Mgmin = self.file_manager.parametres_generaux['Mgmin']
            PFCmax = self.file_manager.parametres_generaux['PFCmax']
            PPT = self.file_manager.BoutonsEtParamètres['PPT']
            self.plot_manager.update_figure(self.Mg, self.PFC, self.timedata, self.Mgdata, self.PFCdata, Mgmin, PFCmax, PPT)
        self.t += 1

    def run_simulation(self, interval=1):
        """Démarre la simulation après initialisation, en utilisant un timer pour le cycle de simulation."""
        self.file_manager.read_parametres_generaux()
        self.initialize_simulation()

        # Démarrage du timer avec l'intervalle en millisecondes
        self.timer.start(interval)

    def handle_poche(self):
        """Gère les événements liés à la poche de magnésium."""
        if self.file_manager.DemandePoche:
            self.handle_message("DemandePoche")
            self.file_manager.DemandePoche = False
        if self.file_manager.AjoutPoche:
            self.Mg = self.file_manager.parametres_generaux["Mgmax"]
            self.PFC += self.file_manager.BoutonsEtParamètres["PPT"]
            self.handle_message("AjoutPoche")
            self.file_manager.AjoutPoche = False


    def handle_message(self, event):
        """Gère l'affichage des messages selon l'événement fourni."""
        if event == "DemandePoche":

            liste_quantites_moules_a_produire = self.file_manager.ProgrammeDISA["Nb Moules"]
            liste_masses_grappes_moules = self.file_manager.ProgrammeDISA["Poids"]
            liste_cadences_moule_par_heure = self.file_manager.ProgrammeDISA["Cadences"]
            

            R = self.file_manager.parametres_generaux['R']
            masse_fil = self.file_manager.parametres_generaux['masse_fil']
            masse_mg_fil = self.file_manager.parametres_generaux['masse_mg_fil']
            PFCmin = self.file_manager.parametres_generaux['PFCmin']
            Mgmin = self.file_manager.parametres_generaux['Mgmin']
            Mgmax = self.file_manager.parametres_generaux['Mgmax']
            eC = self.file_manager.parametres_generaux['eC']
            eP = self.file_manager.parametres_generaux['eP']
            temps_traitement = self.file_manager.parametres_generaux['temps_traitement']
            temps_gs = self.file_manager.parametres_generaux['temps_gs']
            temps_serie = self.file_manager.parametres_generaux['temps_serie']


            PPT = self.file_manager.BoutonsEtParamètres['PPT']
            S = self.file_manager.BoutonsEtParamètres['S']
            TPT = self.file_manager.BoutonsEtParamètres['TPT']



            delai_avt_traitement, Mglimite, PFClimite = calcul_temps_limite(self.PFC, self.Mg, PFCmin, Mgmin, eC, temps_traitement, temps_serie, liste_masses_grappes_moules, liste_cadences_moule_par_heure, liste_quantites_moules_a_produire)
            K, L = calcul_longueur_fil(PPT, S, temps_gs, TPT, R, masse_fil, 
                                       masse_mg_fil, Mgmax, eP, PFClimite, Mglimite)
            

            message = (f"Lancer la poche dans {delai_avt_traitement} minutes avec cette longueur "
                       f"de fil fourée {L} m pour une visée de {K} en %")
        elif event == "AjoutPoche":
            message = "On a ajouté la poche maintenant"
        else:
            message = "Aucun message"
        
        self.update_message(message)


    def pendant_consommation(self, Mg, PFC):
        # Constantes dans ce programme
        eC = self.file_manager.parametres_generaux['eC']

        # Variables dans ce programme
        liste_quantites_moules_a_produire = self.file_manager.ProgrammeDISA["Nb Moules"]
        liste_masses_grappes_moules = self.file_manager.ProgrammeDISA["Poids"]
        liste_cadences_moule_par_heure = self.file_manager.ProgrammeDISA["Cadences"]

        global message

        # On produit les moules !! 
        masse_grappe_i = liste_masses_grappes_moules[0]
        cadence_moule_par_heure_i = liste_cadences_moule_par_heure[0]
        quantite_moules_a_produire_i = liste_quantites_moules_a_produire[0]
        
        # La cadence de consommation en kg/min du i-ème modèle
        cadence_fonte_i = cadence_moule_par_heure_i / 60 * masse_grappe_i  # en kg/min
        
        # Quantités de moules du i-ème modèle produits en une minute
        # cadence_moule_i = int(cadence_fonte_i / masse_grappe_i) # en unités/min
        cadence_moule_i = cadence_fonte_i / masse_grappe_i # en unités/min
        
        # Mise à jour du pourcentage de Mg et du poids fonte coulée
        PFC -= cadence_fonte_i
        Mg -= eC

        # On met à jour le programme de productions des moules
        liste_quantites_moules_a_produire[0] -= cadence_moule_i

        if liste_quantites_moules_a_produire[0] <= 0 :
            message ="On a théoriquement finis de produire ce modèle, passons au modèle suivant !"

        # On reste dans l'état consom tant que l'utilisateur ne dit pas de changer de Série
        etat_suivant= "etat_Consom"

        # Si on a fini de tout produire alors on stoppe la procédure 
        # On passe à l'état Fin
        if not liste_masses_grappes_moules:
            etat_suivant = "etat_Fin"
        
        return Mg, PFC, etat_suivant

    def pendant_changement_serie(self, Mg, PFC):
        # Constantes dans ce programme
        eC = self.file_manager.parametres_generaux['eC']
        
        # Variables dans ce programme
        temps_serie = self.file_manager.parametres_generaux['temps_serie']
        liste_quantites_moules_a_produire = self.file_manager.ProgrammeDISA["Nb Moules"]
        liste_masses_grappes_moules = self.file_manager.ProgrammeDISA["Poids"]
        liste_cadences_moule_par_heure = self.file_manager.ProgrammeDISA["Cadences"]


        temps_serie_courant = self.file_manager.parametres_generaux['temps_serie_courant']

        global message


        if temps_serie_courant == temps_serie :

            # Suppression des éléments déjà traités dans les listes
            liste_masses_grappes_moules.pop(0)
            liste_quantites_moules_a_produire.pop(0)
            liste_cadences_moule_par_heure.pop(0)
            
        # pendant Temps_Serie :
        Mg -= eC # perte de Mg par minute ou par seconde
        temps_serie_courant -= 1 # pas de temps en minute
       
        etat_suivant = "etat_Serie"


        if temps_serie_courant == 0:
            temps_serie_courant = temps_serie  # Réinitialiser le temps de série
            

            message ="On a finis le changement de modèle, commençons le prochain modèle !"

            etat_suivant = "etat_Consom"


        self.file_manager.parametres_generaux['temps_serie_courant'] = temps_serie_courant
        
        return Mg, PFC, etat_suivant

    def pendant_panne(self, Mg, PFC):
        # Variables dans ce programme
        Panne =  self.file_manager.Panne

        # Constantes dans ce programme
        eC = self.file_manager.parametres_generaux['eC']


        # pendant Temps_Panne non définis :
        Mg -= eC # perte de Mg par minute ou par seconde


        etat_suivant = "etat_Panne"
        if not Panne :
            etat_suivant = "etat_Consom"
        
        return Mg, PFC, etat_suivant

    def handle_state(self, etat_courant):
        """Gère les transitions d'états selon l'état courant."""
        if etat_courant == "etat_Consom":
            self.Mg, self.PFC, etat_suivant = self.pendant_consommation(self.Mg, self.PFC)
        elif etat_courant == "etat_Serie":
            self.Mg, self.PFC, etat_suivant = self.pendant_changement_serie(self.Mg, self.PFC)
        elif etat_courant == "etat_Panne":
            self.Mg, self.PFC, etat_suivant = self.pendant_panne(self.Mg, self.PFC)
        elif etat_courant == "etat_Fin":
            self.file_manager.running = False
            etat_suivant = "etat_Fin"
        return etat_suivant

    def record_data(self):
        """Enregistre les données de simulation pour suivi et affichage."""
        self.timedata.append(self.t)
        self.Mgdata.append(self.Mg)
        self.PFCdata.append(self.PFC)



    def update_message(self, message):
        """Affiche ou enregistre le message pour le suivi utilisateur."""
        print(message)  # À personnaliser selon votre affichage (widgets, logs, etc.)


# Intégration PyQt5 pour lancer l'application
if __name__ == "__main__":
    chemin_ParamètresGénéraux = 'ParamètresGénéraux.CSV'
    chemin_BoutonsEtParamètres = 'BoutonsEtParamètres.CSV'
    chemin_ProgrammeDISA = 'ProgrammeDISA.CSV'

    app = QApplication(sys.argv)
    sim = Simulation(chemin_ParamètresGénéraux, chemin_BoutonsEtParamètres, chemin_ProgrammeDISA)
    sim.run_simulation()  # Démarre la simulation avec un intervalle de 1000 ms (1 seconde)
    sim.show()

    sys.exit(app.exec_())







