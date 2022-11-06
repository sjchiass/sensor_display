from pms5003 import PMS5003, SerialTimeoutError, ChecksumMismatchError
import pandas as pd
import os.path
import time
import datetime

# This code is from the PMS5003 example from Pimonori:
# https://github.com/pimoroni/pms5003-python/blob/master/examples/all.py
print("Initializing PMS5003 ...")
pms5003 = PMS5003(
    device='/dev/ttyAMA0',
    baudrate=9600,
    pin_enable=22,
    pin_reset=27
)
print("Sensors initialized!")

def get_particulate():
    while True:
        try:
            return list(pms5003.read().data[:12])
        except SerialTimeoutError as e:
            print(e)
            pass
        except ChecksumMismatchError as e:
            print(e)
            pass
    time.sleep(5)

# Generate a dictionary of data for all sensor values
def data_current():
    labels = ["dt", "pm1", "pm2_5", "pm10", "pm1_atmos", "pm2_5_atmos", "pm10_atmos",
              "0_3um", "0_5um", "1_0um", "2_5um", "5_0um", "10um"]
    values = [datetime.datetime.now()] + get_particulate()
    data = {k:v for k,v in zip(labels, values)}
    return data

# Below, the paths assume this repo is in ~, which is where the user systemd
# services start from
# Clean up file by averaging data to minutes, saves space
if os.path.isfile("./sensor_display/pms5003_data.csv"):
    df = pd.read_csv("./sensor_display/pms5003_data.csv")
    df["dt"] = pd.to_datetime(df["dt"])
    df = df.set_index("dt")
    df = df.sort_index()
    df = df.resample("min").mean().round(0).dropna()
    df.to_csv("./sensor_display/pms5003_data.csv")

# Main loop
while True:
    # Make a new row of data
    df = pd.DataFrame([data_current()])
    # If there is already a data file, append to it only
    if os.path.isfile("./sensor_display/pms5003_data.csv"):
        df.to_csv("./sensor_display/pms5003_data.csv", mode="a", index=False, header=False)
    else:
        # Otherwise start a new file
        df.to_csv("./sensor_display/pms5003_data.csv", index=False)
    time.sleep(1)
