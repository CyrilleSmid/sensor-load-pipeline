from sensor_simulation import simulate_client
import socket
import json
import multiprocessing
import logging as log
log.basicConfig(level=log.INFO)
import time

running_user_ids = []

def handle_new_user(user_data):
    user_id = user_data['user_id']
    last_timestamp = user_data['last_timestamp']
    global running_user_ids
    
    if user_id in running_user_ids:
        log.info(f"User: {user_id} already running")
    else: 
        running_user_ids.append(user_id)
        log.info(f"Starting simulation process for client-{user_id} | Last Timestamp: {last_timestamp}")
        process = multiprocessing.Process(target=simulate_client, args=(user_id, last_timestamp))
        process.start()

def start_socket_server():
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
                    handle_new_user(user_data)

if __name__ == "__main__":
    log.info(f"Starting client sensor simulator manager")
    
    start_socket_server()
 