import socket
import json
import time
import threading
import logging as log

HOST = 'sensor_simulation'
PORT = 9999  

# Connection retry mechanism
MAX_RETRIES = 5
RETRY_DELAY = 5  # seconds

def connect_with_retry(host, port, user_data):
    retries = 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        while retries < MAX_RETRIES:
            try:
                client.connect((host, port))
                log.info("Connected successfully to {}:{}".format(host, port))
                client.sendall(json.dumps(user_data).encode())
                break  # Exit the loop if connection succeeds
            except Exception as e:
                log.info("Connection failed (retry {}/{}): {}".format(retries+1, MAX_RETRIES, e))
                retries += 1
                time.sleep(RETRY_DELAY)
        else:
            log.info("Failed to connect after {} retries.".format(MAX_RETRIES))

def send_user_info_to_client_manager(user_id, last_timestamp):
    user_data = {
        'user_id': user_id,
        'last_timestamp': last_timestamp
    }
    
    log.info(f"Trying to connect to user: {user_id}")
    retry_thread = threading.Thread(target=connect_with_retry, args=(HOST, PORT, user_data))
    retry_thread.start()