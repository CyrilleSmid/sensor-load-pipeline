import simpy
import pandas as pd
import logging as log

# Define constants
TIME_FACTOR =  0.00015 # 1/60
SIMULATION_TIME = None  # Simulation time in seconds
DATA_INTERVAL = 60*60  # Interval for sending data from each device in seconds
INITIAL_DATA_INTERVAL = 1 # DATA_INTERVAL 

MQTT_TOPIC = 'sensors/electricity'  # Topic to publish data to

def device(env, device_id, client_id, cur_time_index, mqtt_client, data_source):
    sensor_labels = data_source.columns[device_id].split('_')

    sensor_label_key_value = {
        "device_id":device_id,
        "client_id":client_id,
        "floor":sensor_labels[0][-1],
        "zone":sensor_labels[1][-1],
        "sensor":sensor_labels[2],
    }
    
    while cur_time_index < data_source.shape[0]:
        line_protocol = fetch_device_data(device_id, sensor_label_key_value, data_source, cur_time_index)
        
        log.info(f"Published: {line_protocol}")
        mqtt_client.publish(MQTT_TOPIC, line_protocol)
        
        yield env.timeout(INITIAL_DATA_INTERVAL if cur_time_index < 24*95 else DATA_INTERVAL)
        cur_time_index += 1
    log.info(f"All data processed")


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

def simulation(env, user_id, last_timestamp, mqtt_client):
    client_id = f'client-{user_id}'    
    
    path = 'data/clean_merged_dataset.csv'
    sensor_data = pd.read_csv(path, parse_dates=['Date']).set_index('Date')
    num_sensors = len(sensor_data.columns)
    
    cur_time_index = 0
    if last_timestamp != "None":
        last_timestamp=pd.to_datetime(last_timestamp)
        cur_time_index = max(sensor_data.index.get_loc(last_timestamp, method='nearest') - 12, 0)
        log.info(f"Recovered current time index: {sensor_data.index[cur_time_index]}")
    
    devices = [env.process(device(env, i, client_id, cur_time_index, mqtt_client, sensor_data)) for i in range(num_sensors)]
    if SIMULATION_TIME is not None:
        yield env.timeout(SIMULATION_TIME)

def simulate_client(user_id, last_timestamp, mqtt_client):
    env = simpy.rt.RealtimeEnvironment(factor=TIME_FACTOR, strict=False)
    env.process(simulation(env, user_id, last_timestamp, mqtt_client))
    env.run(until=SIMULATION_TIME)
    return env
