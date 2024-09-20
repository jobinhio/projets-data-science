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
