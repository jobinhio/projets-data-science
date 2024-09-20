import time
from file_io import FileManager
from plotting import PlotManager
from utils import calcul_temps_limite, calcul_longueur_fil



class Simulation:
    def __init__(self, param_file, button_file, disa_file):
        # FileManager s'occupe de la lecture et de la gestion des fichiers
        self.file_manager = FileManager(param_file, button_file, disa_file)

        # Paramètres généraux et DISA non initialisés directement
        self.params_generaux = None
        self.programme_disa = None
        self.boutons_et_parametres = None

        # Initialisation du gestionnaire de plots
        self.plot_manager = PlotManager()

        # Variables de simulation
        self.Mg = 0.045  # Quantité initiale de magnésium
        self.PFC = 3500  # Poids de fonte coulée initial
        self.t = 0  # Temps de simulation
        self.timedata = []
        self.Mgdata = []
        self.PFCdata = []

    def initialize_simulation(self):
        """Initialise la simulation en lisant les fichiers nécessaires via FileManager."""
        self.params_generaux = self.file_manager.read_parametres_generaux()
        self.programme_disa = self.file_manager.read_programme_disa()
        self.boutons_et_parametres = self.file_manager.read_file_boutons_et_parametres()

        if self.params_generaux and self.programme_disa and self.boutons_et_parametres:
            print("Simulation initialisée avec succès.")
        else:
            print("Échec de l'initialisation de la simulation. Vérifiez les fichiers.")

    def step(self):
        """Effectue une étape de la simulation."""
        if self.t != 0:
            self.handle_poche()
            self.file_manager.etat_courant = self.handle_state(self.file_manager.etat_courant)
            self.record_data()
            self.plot_manager.update_figure(self.Mg, self.PFC, self.timedata, self.Mgdata, self.PFCdata)
        self.t += 1

    def run_simulation(self, interval=1):
        """Démarre la simulation après initialisation."""
        self.file_manager.read_parametres_generaux()
        self.initialize_simulation()

        while self.file_manager.etat_courant != "etat_Fin":
            try:
                self.file_manager.check_for_updates()
                if self.file_manager.running:
                    self.step()
            except FileNotFoundError as e:
                print(f"Erreur : {e}")
            except Exception as e:
                print(f"Une erreur est survenue : {e}")
            time.sleep(interval)

    def handle_poche(self):
        """Gère les événements liés à la poche de magnésium."""
        if self.file_manager.DemandePoche:
            self.handle_message("DemandePoche")
            self.file_manager.DemandePoche = False
        if self.file_manager.AjoutPoche:
            self.Mg = self.Mgmax
            self.PFC += self.PPT
            self.handle_message("AjoutPoche")
            self.file_manager.AjoutPoche = False

    def handle_message(self, event):
        """Gère l'affichage des messages selon l'événement fourni."""
        if event == "DemandePoche":
            delai_avt_traitement, Mglimite, PFClimite = calcul_temps_limite(self.PFC, self.Mg)
            K, L = calcul_longueur_fil(self.PPT, self.S, self.TPT, self.R, self.masse_fil, 
                                       self.masse_mg_fil, self.Mgmax, self.eP, PFClimite, Mglimite)
            message = (f"Lancer la poche dans {delai_avt_traitement} minutes avec cette longueur "
                       f"de fil fourée {L} m pour une visée de {K} en %")
        elif event == "AjoutPoche":
            message = "On a ajouté la poche maintenant"
        else:
            message = "Aucun message"
        
        self.update_message(message)


    def pendant_consommation(self, Mg, PFC):
        # Constantes dans ce programme
        eC = self.parametres_generaux['eC']

        # Variables dans ce programme
        liste_quantites_moules_a_produire = self.ProgrammeDISA["Nb Moules"]
        liste_masses_grappes_moules = self.ProgrammeDISA["Poids"]
        liste_cadences_moule_par_heure = self.ProgrammeDISA["Cadences"]

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
        eC = self.parametres_generaux['eC']
        
        # Variables dans ce programme
        temps_serie = self.parametres_generaux['temps_serie']
        liste_quantites_moules_a_produire = self.ProgrammeDISA["Nb Moules"]
        liste_masses_grappes_moules = self.ProgrammeDISA["Poids"]
        liste_cadences_moule_par_heure = self.ProgrammeDISA["Cadences"]

        global message, temps_serie_courant


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
        
        return Mg, PFC, etat_suivant

    def pendant_panne(self, Mg, PFC):
        # Variables dans ce programme
        Panne =  self.Panne

        # Constantes dans ce programme
        eC = self.parametres_generaux['eC']


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
            self.running = False
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

