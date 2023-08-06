import socket
import threading

def handle_client(client_socket, player_number):
    while True:
        # Receive a message from the client
        msg = client_socket.recv(1024).decode('utf-8')

        # If msg is empty, the client has disconnected
        if not msg:
            break

        print(f'Player {player_number}: {msg}')

    # Close the client socket
    client_socket.close()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    server_socket.bind(('0.0.0.0', 12345))
except:
    print("address 12345 already in use")
server_socket.listen()

player_counter = 0
while True:
    # Wait for a client to connect
    client_socket, address = server_socket.accept()
    print(f'Accepted connection from {address}, assigned to Player {player_counter}')

    # Start a new thread to handle the client
    threading.Thread(target=handle_client, args=(client_socket, player_counter)).start()

    player_counter += 1