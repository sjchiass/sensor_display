from sgp30 import SGP30
import sys
import pandas as pd
import os.path
import time
import datetime

# This code is from the Pimoroni example:
# https://github.com/pimoroni/sgp30-python/blob/master/examples/test.py
# Initial the dht device, with data pin connected to:
print("Initializing SGP30 ...")
sgp30 = SGP30()
print("Sensor warming up, please wait...")
def crude_progress_bar():
    sys.stdout.write('.')
    sys.stdout.flush()
sgp30.start_measurement(crude_progress_bar)
sys.stdout.write('\n')
print("Sensors initialized!")

def get_sgp30():
    result = sgp30.get_air_quality()
    return [result.equivalent_co2, result.total_voc]

# Generate a dictionary of data for all sensor values
def data_current():
    labels = ["dt", "eco2", "voc"]
    values = [datetime.datetime.now()] + get_sgp30()
    data = {k:v for k,v in zip(labels, values)}
    return data

# Below, the paths assume this repo is in ~, which is where the user systemd
# services start from
# Clean up file by averaging data to minutes, saves space
if os.path.isfile("./sensor_display/sgp30_data.csv"):
    df = pd.read_csv("./sensor_display/sgp30_data.csv")
    df["dt"] = pd.to_datetime(df["dt"])
    df = df.set_index("dt")
    df = df.sort_index()
    df = df.resample("min").mean().round(0).dropna()
    df.to_csv("./sensor_display/sgp30_data.csv")

# Main loop
while True:
    # Make a new row of data
    time.sleep(1.0)
    df = pd.DataFrame([data_current()])
    # If there is already a data file, append to it only
    if os.path.isfile("./sensor_display/sgp30_data.csv"):
        df.to_csv("./sensor_display/sgp30_data.csv", mode="a", index=False, header=False)
    else:
        # Otherwise start a new file
        df.to_csv("./sensor_display/sgp30_data.csv", index=False)
