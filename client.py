import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 12345))

while True:
    # Get a message from the user
    msg = input('Enter a message: ')

    # If msg is "quit", break the loop and disconnect
    if msg.lower() == 'quit':
        break

    # Send the message to the server
    client_socket.send(msg.encode('utf-8'))

# Close the client socket
client_socket.close()
