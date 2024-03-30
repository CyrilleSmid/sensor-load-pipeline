import simpy
import numpy as np
import pandas as pd
import json
import logging as log
import paho.mqtt.client as mqtt
import random

# Define constants
TIME_FACTOR = 0.001
SIMULATION_TIME = 60*60*72  # Simulation time in seconds
DATA_INTERVAL = 60*60  # Interval for sending data from each device in seconds

# MQTT Broker (HiveMQ) configuration
client_id = f'client-{random.randint(0, 1000)}'
MQTT_BROKER = 'localhost'  # Change to your HiveMQ broker address
MQTT_PORT = 1883  # Default MQTT port
MQTT_TOPIC = 'sensors/electricity'  # Topic to publish data to

def device(env, device_id, mqtt_client, data_source):
    sensor_labels = data_source.columns[device_id].split('_')

    # sensor_label_key_value = f'floor:"{sensor_labels[0][-1]}", zone:"{sensor_labels[1][-1]}", sensor:"{sensor_labels[2]}"'
    sensor_label_key_value = {
        "device_id":device_id,
        "client_id":client_id,
        "floor":sensor_labels[0][-1],
        "zone":sensor_labels[1][-1],
        "sensor":sensor_labels[2],
    }
    
    cur_time_index = 0
    while True:
        line_protocol = fetch_device_data(device_id, sensor_label_key_value, data_source, cur_time_index)
        
        log.info(f"Published: {line_protocol}")
        print(f"Published: {line_protocol}")
        mqtt_client.publish(MQTT_TOPIC, line_protocol)
        
        yield env.timeout(DATA_INTERVAL)
        cur_time_index += 1


def fetch_device_data(device_id, sensor_label_key_value, data_source, cur_time_index):
        data = data_source.iloc[cur_time_index, device_id]
        measurement_time = data_source.index[cur_time_index]
        
        # prometheus_data = f'electricity_load{{device_id="{device_id}", client_id="{client_id}", {sensor_label_key_value}}} {data} {cur_time.timestamp()}'

        # Construct the line protocol string
        line_protocol = "sensors"

        # Add tags
        tags = [f"{tag_key}={tag_value}" for tag_key, tag_value in sensor_label_key_value.items()]
        if tags:
            line_protocol += "," + ",".join(tags)

        # Add fields
        field = f"electricity_load={data}"
        line_protocol += " " + field

        # Add timestamp
        line_protocol += " " + str(measurement_time.value)  # Convert to nanoseconds
        
        return line_protocol

def simulation(env):
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)  # MQTT client
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)  # Connect to MQTT broker
    
    path = 'C:\dev\Projects\sensor-load-pipeline\sensor_simulation\data\clean_merged_dataset.csv' # 'data/clean_merged_dataset.csv'
    sensor_data = pd.read_csv(path, parse_dates=['Date']).set_index('Date')
    num_sensors = len(sensor_data.columns)
    
    devices = [env.process(device(env, i, mqtt_client, sensor_data)) for i in range(num_sensors)] 
    yield env.timeout(SIMULATION_TIME)

env = simpy.rt.RealtimeEnvironment(factor=TIME_FACTOR, strict=False)
env.process(simulation(env))
env.run(until=SIMULATION_TIME)