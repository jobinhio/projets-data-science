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








class PlotManager:
    def __init__(self):
        self.fig_Mg, self.scatter_Mg = self.create_plot("Consommation de Mg", "Temps", "Mg")
        self.fig_PFC, self.scatter_PFC = self.create_plot("Consommation de Fonte", "Temps", "Fonte")

    def create_plot(self, title, xaxis_title, yaxis_title):
        fig = go.FigureWidget()
        scatter = fig.add_scatter(mode='lines+markers').data[0]
        fig.update_layout(title=title, xaxis_title=xaxis_title, yaxis_title=yaxis_title)
        display(fig)
        return fig, scatter

    def update_plot_data(self, fig, scatter, xdata, ydata):
        with fig.batch_update():
            scatter.update(x=xdata, y=ydata)

    def add_colored_segment(self, fig, x0, x1, y0, y1, color):
        segment = go.Scatter(x=[x0, x1], y=[y0, y1], mode='lines+markers', line=dict(color=color), showlegend=False)
        with fig.batch_update():
            fig.add_trace(segment)

    def determine_segment_color(self, Mg, PFC, Mgmin, PFCmax, PPT):
        if (PFC + PPT) >= PFCmax and Mg <= Mgmin:
            return 'red'
        elif (PFC + PPT) <= PFCmax and Mg <= Mgmin:
            return 'orange'
        else:
            return 'green'

    def update_figure(self, Mg, PFC, timedata, Mgdata, PFCdata):
        self.update_plot_data(self.fig_PFC, self.scatter_PFC, timedata, PFCdata)
        if len(timedata) >= 2:
            x0, x1 = timedata[-2], timedata[-1]
            y0, y1 = Mgdata[-2], Mgdata[-1]
            color = self.determine_segment_color(Mg, PFC)
            self.add_colored_segment(self.fig_Mg, x0, x1, y0, y1, color)
