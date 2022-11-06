import adafruit_dht
import board
import pandas as pd
import os.path
import time
import datetime

# This is the adafrtui example code from here:
# https://learn.adafruit.com/dht-humidity-sensing-on-raspberry-pi-with-gdocs-logging/python-setup
# Initial the dht device, with data pin connected to:
print("Initializing DHT22 ...")
dhtDevice = adafruit_dht.DHT22(board.D18)
print("Sensors initialized!")

def get_dht22():
    while True:
        try:
            # Print the values to the serial port
            temperature_c = dhtDevice.temperature
            humidity = dhtDevice.humidity
        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            print(datetime.datetime.now(), error.args[0])
            time.sleep(2.0)
            continue
        except Exception as error:
            dhtDevice.exit()
            raise error
        time.sleep(2.0)
        return [temperature_c, humidity]

# Generate a dictionary of data to make into a dataframe
def data_current():
    labels = ["dt", "temperature", "humidity"]
    values = [datetime.datetime.now()] + get_dht22()
    data = {k:v for k,v in zip(labels, values)}
    return data

# Below, the paths assume this repo is in ~, which is where the user systemd
# services start from
# Clean up file by averaging data to minutes, saves space
if os.path.isfile("./sensor_display/dht22_data.csv"):
    df = pd.read_csv("./sensor_display/dht22_data.csv")
    df["dt"] = pd.to_datetime(df["dt"])
    df = df.set_index("dt")
    df = df.sort_index()
    df = df.resample("min").mean().round(1).dropna()
    df.to_csv("./sensor_display/dht22_data.csv")

# Main loop
while True:
    # Make a new row of data
    df = pd.DataFrame([data_current()])
    # If there is already a data file, append to it only
    if os.path.isfile("./sensor_display/dht22_data.csv"):
        df.to_csv("./sensor_display/dht22_data.csv", mode="a", index=False, header=False)
    else:
        # Otherwise start a new file
        df.to_csv("./sensor_display/dht22_data.csv", index=False)
