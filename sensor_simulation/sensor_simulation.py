import simpy
import numpy as np
import pandas as pd
import json
import paho.mqtt.client as mqtt
import random

# Define constants
TIME_FACTOR = 0.001
SIMULATION_TIME = 60*60*3  # Simulation time in seconds
DATA_INTERVAL = 60*60  # Interval for sending data from each device in seconds

# MQTT Broker (HiveMQ) configuration
client_id = f'client-{random.randint(0, 1000)}'
MQTT_BROKER = 'localhost'  # Change to your HiveMQ broker address
MQTT_PORT = 1883  # Default MQTT port
MQTT_TOPIC = 'sensors/electricity'  # Topic to publish data to

def device(env, device_id, mqtt_client, data_source):
    sensor_labels = data_source.columns[device_id].split('_')
    sensor_label_key_value = f'floor:"{sensor_labels[0][-1]}", zone:"{sensor_labels[1][-1]}", sensor:"{sensor_labels[2]}"'
    cur_time_index = 0
    while True:
        data = data_source.iloc[cur_time_index, device_id]
        cur_time = data_source.index[cur_time_index]
        
        send_data_to_mqtt(mqtt_client, cur_time, device_id, data, sensor_label_key_value)
        yield env.timeout(DATA_INTERVAL)
        cur_time_index += 1

def send_data_to_mqtt(mqtt_client, time, device_id, data, sensor_label_key_value): 
    prometheus_data = f'electricity_load{{device_id="{device_id}", client_id="{client_id}", {sensor_label_key_value}}} {data} {time.timestamp()}'
    print(prometheus_data)
    mqtt_client.publish(MQTT_TOPIC, prometheus_data)

def simulation(env):
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)  # MQTT client
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)  # Connect to MQTT broker
    
    path = 'C:\dev\Projects\sensor-load-pipeline\sensor_simulation\data\clean_merged_dataset.csv' # 'data/clean_merged_dataset.csv'
    sensor_data = pd.read_csv(path, parse_dates=['Date']).set_index('Date')
    num_sensors = len(sensor_data.columns)
    
    devices = [env.process(device(env, i, mqtt_client, sensor_data)) for i in range(3)] 
    yield env.timeout(SIMULATION_TIME)

env = simpy.rt.RealtimeEnvironment(factor=TIME_FACTOR, strict=False)
env.process(simulation(env))
env.run(until=SIMULATION_TIME)
