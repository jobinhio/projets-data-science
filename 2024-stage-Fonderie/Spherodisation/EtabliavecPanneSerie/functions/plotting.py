# import plotly.graph_objects as go
# from IPython.display import display
# import time


# class PlotManager:
#     def __init__(self):
#         self.fig_Mg, self.scatter_Mg = self.create_plot("Consommation de Mg", "Temps", "Mg")
#         self.fig_PFC, self.scatter_PFC = self.create_plot("Consommation de Fonte", "Temps", "Fonte")

#     def create_plot(self, title, xaxis_title, yaxis_title):
#         fig = go.FigureWidget()
#         scatter = fig.add_scatter(mode='lines+markers').data[0]
#         fig.update_layout(title=title, xaxis_title=xaxis_title, yaxis_title=yaxis_title)
#         display(fig)
#         return fig, scatter

#     def update_plot_data(self, fig, scatter, xdata, ydata):
#         with fig.batch_update():
#             scatter.update(x=xdata, y=ydata)

#     def add_colored_segment(self, fig, x0, x1, y0, y1, color):
#         segment = go.Scatter(x=[x0, x1], y=[y0, y1], mode='lines+markers', line=dict(color=color), showlegend=False)
#         with fig.batch_update():
#             fig.add_trace(segment)

#     def determine_segment_color(self, Mg, PFC, Mgmin, PFCmax, PPT):
#         if (PFC + PPT) >= PFCmax and Mg <= Mgmin:
#             return 'red'
#         elif (PFC + PPT) <= PFCmax and Mg <= Mgmin:
#             return 'orange'
#         else:
#             return 'green'

#     def update_figure(self, Mg, PFC, timedata, Mgdata, PFCdata, Mgmin, PFCmax, PPT):
#         self.update_plot_data(self.fig_PFC, self.scatter_PFC, timedata, PFCdata)
#         if len(timedata) >= 2:
#             x0, x1 = timedata[-2], timedata[-1]
#             y0, y1 = Mgdata[-2], Mgdata[-1]
#             color = self.determine_segment_color(Mg, PFC, Mgmin, PFCmax, PPT) 
#             self.add_colored_segment(self.fig_Mg, x0, x1, y0, y1, color)



#------------------------------------------------

import plotly.graph_objs as go
from IPython.display import display





import ipywidgets as widgets

message_output = widgets.Output()
message = "Aucun Message"

def initialize_message():
    """Initialise le widget Output avec un fond blanc et pas de message."""
    with message_output:
        message_output.clear_output()
        display(widgets.HTML(
            "<div style='background-color:white; color:black; font-size:20px; padding:10px; text-align:center;'>"
            "Aucun message</div>"
        ))

    display(message_output)

def update_message(message):
    """Met à jour le message affiché avec un style personnalisé."""
    with message_output:
        message_output.clear_output()  # Efface les anciens messages
        display(widgets.HTML(
            f"<div style='background-color:yellow; color:red; font-size:24px; font-weight:bold; "
            f"border:2px solid black; padding:10px; text-align:center;'>"
            f"{message}</div>"
        ))






#-----------------------------------------



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

