import simpy
import numpy as np
import pandas as pd
import json
import logging as log
import paho.mqtt.client as mqtt
import random
import os
import multiprocessing    
import time

# Define constants
TIME_FACTOR = 0.00001
SIMULATION_TIME = None  # Simulation time in seconds
DATA_INTERVAL = 60*60  # Interval for sending data from each device in seconds

# MQTT Broker (HiveMQ) configuration
MQTT_BROKER = 'mqtt_broker'  # Change to your HiveMQ broker address
MQTT_PORT = 1883  # Default MQTT port
MQTT_TOPIC = 'sensors/electricity'  # Topic to publish data to

# Connection retry mechanism
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds

def device(env, device_id, client_id, last_timestamp, mqtt_client, data_source):
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
    if last_timestamp is not None: 
        # TODO: recover current time index
        pass 
    while True:
        line_protocol = fetch_device_data(device_id, sensor_label_key_value, data_source, cur_time_index)
        
        # log.info(f"Published: {line_protocol}")
        mqtt_client.publish(MQTT_TOPIC, line_protocol)
        
        yield env.timeout(DATA_INTERVAL)
        cur_time_index += 1


def fetch_device_data(device_id, sensor_label_key_value, data_source, cur_time_index):
        data = data_source.iloc[cur_time_index, device_id]
        measurement_time = data_source.index[cur_time_index]

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

def simulation(env, user_id, last_timestamp):
    client_id = f'client-{user_id}'
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=str(user_id))  # MQTT client
    
    retries = 0
    while retries < MAX_RETRIES:
        try:
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT)  # Connect to MQTT broker
            log.info("Connected successfully to {}:{}".format(MQTT_BROKER, MQTT_PORT))
            break  # Exit the loop if connection succeeds
        except Exception as e:
            log.info("Connection failed (retry {}/{}): {}".format(retries+1, MAX_RETRIES, e))
            retries += 1
            time.sleep(RETRY_DELAY)
    else:
        log.info("Failed to connect after {} retries.".format(MAX_RETRIES))
    
    
    path = 'data/clean_merged_dataset.csv'
    sensor_data = pd.read_csv(path, parse_dates=['Date']).set_index('Date')
    num_sensors = len(sensor_data.columns)
    
    devices = [env.process(device(env, i, client_id, last_timestamp, mqtt_client, sensor_data)) for i in range(num_sensors)]
    if SIMULATION_TIME is not None:
        yield env.timeout(SIMULATION_TIME)

def simulate_client(user_id, last_timestamp):
    env = simpy.rt.RealtimeEnvironment(factor=TIME_FACTOR, strict=False)
    env.process(simulation(env, user_id, last_timestamp))
    env.run(until=SIMULATION_TIME)
    return env
