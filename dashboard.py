import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import os

# Read in the data
# With the systemd user services, the script will expect to be in a folder
# in the user home folder
df_dht22 = pd.read_csv("./sensor_display/dht22_data.csv")
df_sgp30 = pd.read_csv("./sensor_display/sgp30_data.csv")
df_pms5003 = pd.read_csv("./sensor_display/pms5003_data.csv")

# This is a function to only read the last line of data, so that your SD card
# is not read too many times.
# Code is from here: https://stackoverflow.com/a/68413780
def data_current(filename):
    with open(filename, "rb") as file:
        # Go to the end of the file before the last break-line
        file.seek(-2, os.SEEK_END) 
        # Keep reading backward until you find the next break-line
        while file.read(1) != b'\n':
            file.seek(-2, os.SEEK_CUR) 
        data = file.readline().decode()
    data = data.replace("\n", "").split(",")
    for i in range(1, len(data)):
        data[i] = float(data[i])
    data = [data]
    return data

# Set the dashboard UI
app = dash.Dash(__name__)
app.layout = html.Div(
    html.Div([
        dcc.Dropdown(["Graph", "Indicators"], "Indicators", id="visual-type"),
        dcc.Graph(id='live-update-graph'),
        dcc.Interval(
            id='interval-component',
            interval=60000, # in milliseconds
            n_intervals=0
        )
    ])
)


# Generate the graphs
@app.callback(Output('live-update-graph', 'figure'),
              Input('interval-component', 'n_intervals'),
              Input('visual-type', 'value'))
def update_graph_live(n, visual_type):
    # Just to make things easier, keep the data as global variables
    global df_dht22, df_sgp30, df_pms5003
    
    # Combine the old data with new data from the end of the files
    df_dht22 = pd.concat([df_dht22, pd.DataFrame(data_current("./sensor_display/dht22_data.csv"), columns=list(df_dht22))])
    df_sgp30 = pd.concat([df_sgp30, pd.DataFrame(data_current("./sensor_display/sgp30_data.csv"), columns=list(df_sgp30))])
    df_pms5003 = pd.concat([df_pms5003, pd.DataFrame(data_current("./sensor_display/pms5003_data.csv"), columns=list(df_pms5003))])
    
    # Merge all the data
    df = df_dht22.merge(df_sgp30, how="outer", on="dt").merge(df_pms5003, how="outer", on="dt")
    
    # Average of values by each minute
    # Also front-fill any series that is running slow
    averaged = df.copy()
    averaged["dt"] = pd.to_datetime(averaged["dt"])
    averaged = averaged.set_index("dt")
    averaged = averaged.sort_index()
    averaged = averaged.resample("min").mean()
    averaged = averaged.fillna(method="ffill")
    
    # For the gauges, determine the latest datapoints and the ones just before that
    latest = averaged.tail(1)
    previous = averaged.tail(2).head(1)
    
    # For the time series pivot the data
    latest_pivot = pd.melt(latest, value_vars=["pm1", "pm2_5", "pm10",
                                               "pm1_atmos", "pm2_5_atmos", "pm10_atmos", 
                                               "0_3um", "0_5um", "1_0um", "2_5um",
                                               "5_0um", "10um"])
    
    if visual_type == "Graph":
        # Create a 5-row subplot
        fig = make_subplots(rows=5, cols=1)

        # Add each trace
        fig.add_trace(go.Scatter(x=averaged.index, y=averaged.temperature,
                      name="Temperature"), row=1, col=1)
        fig.add_trace(go.Scatter(x=averaged.index, y=averaged.humidity,
                      name="Humidity"), row=2, col=1)
        fig.add_trace(go.Scatter(x=averaged.index, y=averaged.eco2,
                      name="Environmental CO2"), row=3, col=1)
        fig.add_trace(go.Scatter(x=averaged.index, y=averaged.voc,
                      name="Voltile Organic Compounds"), row=4, col=1)
        fig.add_trace(go.Scatter(x=averaged.index, y=averaged.pm1,
                      name="PM 1"), row=5, col=1)
        fig.add_trace(go.Scatter(x=averaged.index, y=averaged.pm2_5,
                      name="PM 2.5"), row=5, col=1)
        fig.add_trace(go.Scatter(x=averaged.index, y=averaged.pm10,
                      name="PM 10"), row=5, col=1)
    else:
        # Create a 2-row, 4-col  subplot
        fig = make_subplots(rows=2, cols=4,            
            specs=[[{}, {}, {}, {}],
                   [{"colspan": 4}, None, None, None]]
                   )
        fig.add_trace(go.Indicator(
            title="Temperature",
            value=latest.temperature.item(),
            number = {"suffix": "C"},
            mode="number+delta+gauge",
            delta={'reference': previous.temperature.item(), "valueformat": ".1f"},
            gauge={
                # These give some shading to hint at good values
                # I Googled for what are good values
                'axis': {'range': [-20, 60]},
                'bar': {'color': "black", "thickness": 0.25},
                'steps' : [
                 {'range': [-20, 8], 'color': "#adbce6"},
                 {'range': [8, 20], 'color': "#add8e6"},
                 {'range': [24, 30], 'color': "#ffcccb"},
                 {'range': [30, 60], 'color': "#ff817f"}
                 ]
                },
            domain={'row': 0, 'column': 0}))
        fig.add_trace(go.Indicator(
            title="Humidity",
            value=latest.humidity.item(),
            number = {"suffix": "%"},
            mode="number+delta+gauge",
            delta={'reference': previous.humidity.item(), "valueformat": ".1f"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "black", "thickness": 0.25},
                'steps' : [
                 {'range': [0, 30], 'color': "#e0cc77"},
                 {'range': [40, 100], 'color': "#d4f1f9"}
                 ]
                },
            domain={'row': 0, 'column': 1}))
        fig.add_trace(go.Indicator(
            title="Equivalent CO2",
            value=latest.eco2.item(),
            number = {"suffix": "ppm"},
            mode="number+delta+gauge",
            delta={'reference': previous.eco2.item(), "valueformat": ".1f"},
            gauge={
                'axis': {'range': [0, 2000]},
                'bar': {'color': "black", "thickness": 0.25},
                'steps' : [
                 {'range': [0, 300], 'color': "#fed8b1"},
                 {'range': [500, 700], 'color': "#fed8b1"},
                 {'range': [700, 2000], 'color': "#fdad5c"}
                 ]
                },
            domain={'row': 0, 'column': 2}))
        fig.add_trace(go.Indicator(
            title="Total VOC",
            value=latest.voc.item(),
            number = {"suffix": "ppb"},
            mode="number+delta+gauge",
            delta={'reference': previous.voc.item(), "valueformat": ".1f"},
            gauge={
                'axis': {'range': [0, 2000]},
                'bar': {'color': "black", "thickness": 0.25},
                'steps' : [
                 {'range': [220, 660], 'color': "#fed8b1"},
                 {'range': [660, 2000], 'color': "#fdad5c"}
                 ]
                },
            domain={'row': 0, 'column': 3}))
        fig.add_trace(
            go.Bar(x=[
                "PM1.0 ug/m3 (ultrafine particles)",
                "PM2.5 ug/m3 (combustion particles, organic compounds, metals)",
                "PM10 ug/m3  (dust, pollen, mould spores)",
                "PM1.0 ug/m3 (atmos env)",
                "PM2.5 ug/m3 (atmos env)",
                "PM10 ug/m3 (atmos env)",
                ">0.3um in 0.1L air",
                ">0.5um in 0.1L air",
                ">1.0um in 0.1L air",
                ">2.5um in 0.1L air",
                ">5.0um in 0.1L air",
                ">10um in 0.1L air"
                ], y=latest_pivot.value, text=latest_pivot.round().value), row=2, col=1)
        fig.update_yaxes(title_text="Parts per billion", range=[0, max(max(latest_pivot.value), 1000)], row=2, col=1)
        fig.update_layout(template="none")
            
        fig.update_layout(title="Indicators",
                          grid={'rows': 2, 'columns': 4,
                                'pattern': "independent"})

    return fig

# Start the dashboard, making it accessible on the network (though you should disable
# networking on the Pi since there's not much point to it apart from testing)
if __name__ == '__main__':
    app.run_server(debug=False, port=8050, host="0.0.0.0")
