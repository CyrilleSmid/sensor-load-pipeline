from sensor_simulation import simulate_client
import socket
import json
import multiprocessing
import paho.mqtt.client as mqtt 
import time
import logging as log
log.basicConfig(level=log.INFO)

# MQTT Broker (HiveMQ) configuration
MQTT_BROKER = 'mqtt_broker'  # Change to your HiveMQ broker address
MQTT_PORT = 1883  # Default MQTT port

# Connection retry mechanism
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds

running_user_ids = []

def handle_new_user(user_data, mqtt_client):
    user_id = user_data['user_id']
    last_timestamp = user_data['last_timestamp']
    global running_user_ids
    
    if user_id in running_user_ids:
        log.info(f"User: {user_id} already running")
    else: 
        running_user_ids.append(user_id)
        log.info(f"Starting simulation process for client-{user_id} | Last Timestamp: {last_timestamp}")
        process = multiprocessing.Process(target=simulate_client, args=(user_id, last_timestamp, mqtt_client))
        process.start()

def start_socket_server(mqtt_client):
    host = '0.0.0.0'  # Listen on all available interfaces
    port = 9999  # Choose an available port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print("Socket server started. Listening for incoming connections...")
        while True:
            conn, addr = server_socket.accept()
            with conn:
                print(f"Connected by {addr}")
                user_data = conn.recv(1024)
                if user_data:
                    user_data = json.loads(user_data.decode())
                    handle_new_user(user_data, mqtt_client)

if __name__ == "__main__":
    log.info(f"Starting client sensor simulator manager")
    
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="client_manager")  # MQTT client
    
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
    
    start_socket_server(mqtt_client)
 