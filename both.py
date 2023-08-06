import socket
import threading
import pygame
import numpy as np
import json

clients = []

# define constants
CELL_SIZE = 50
GRID_SIZE = 8
SCREEN_SIZE = GRID_SIZE * CELL_SIZE
WHITE = (255, 255, 255)  # Unclaimed cells are white
BLACK = (0, 0, 0)  # Cell border is black
BORDER_SIZE = 2  # Size of the cell border
BRUSH_SIZE = 5  # Size of the brush

# These colors will be assigned to the clients that connect to the server
PLAYER_COLORS = [(0, 0, 255), (0, 255, 0), (255, 255, 0), (0, 255, 255)]

# server host will take the default red color
playerColor = (255, 0, 0)

# global variables
grid = np.full((GRID_SIZE, GRID_SIZE, 3), WHITE, dtype=int)
gridLocks = np.full((GRID_SIZE, GRID_SIZE), None)



def broadcast(data):
    for client in clients:
        try:
            client.send(data.encode('utf-8'))
        except:
            # If sending fails, client has disconnected
            print("BROADCAST FAILED")
            client.close()
            clients.remove(client)

def processData(data):
    global playerColor
    data = json.loads(data)

    if data["type"] == "setColor":
        playerColor = tuple(data["color"])

    elif data["type"] == "fill":
        x, y = tuple(data["coords"])
        print(f"received cell: {x}, {y}")
        grid[y][x] = tuple(data["color"])
        gridLocks[y][x] = 1

    elif data["type"] == "lock":
        x, y = tuple(data["coords"])
        gridLocks[y][x] = 1

    elif data["type"] == "unlock":
        x, y = tuple(data["coords"])
        gridLocks[y][x] = None

def clientHandler(clientSocket):
    while True:
        try:
            receivedData = clientSocket.recv(1024).decode('utf-8')
            broadcast(receivedData)

            processData(receivedData)

        except Exception as e:
            print(f"Error handling client {clientSocket}: {e}")
            clients.remove(clientSocket)
            clientSocket.close()
            break

def clientUpdate():
    while True:
        try:
            receivedData = clientSocket.recv(1024).decode('utf-8')
            processData(receivedData)

        except Exception as e:
            print(f"Error updating client: {e}")
            clientSocket.close()
            break
    

isServer = False
serverSocket = None
clientSocket = None

# Starts server if not already started and clients join if a host exists
try:
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('0.0.0.0', 12345))
    print("Server is waiting for connections...")
    serverSocket.listen()
    isServer = True
except:
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect(('localhost', 12345))
    print("connected to server")

# Server sets a listening thread for each client (player) connected
if (isServer):
    while True:
        playerCount = input("Enter number of players: ")
        if playerCount.isdigit() and int(playerCount) > 0 and int(playerCount) <= 5:
            playerCount = int(playerCount)
            break
        else:
            print("Please enter a positive integer between 1 and 5")
    while len(clients) < playerCount - 1:
        clientSocket, address = serverSocket.accept()

        colorData = json.dumps({"type": "setColor", "color": PLAYER_COLORS[len(clients)]})
        clientSocket.send(colorData.encode("utf-8"))

        clients.append(clientSocket)
        client_thread = threading.Thread(target=clientHandler, args=(clientSocket,))
        client_thread.start()
        print(f"Connection {len(clients)} established")
    print("all connections established")

# Client sets a thread listening to the server host for updates
else:
    print("Waiting to be assigned color...")
    receivedData = clientSocket.recv(1024).decode('utf-8')

    processData(receivedData)
    # jsonData = json.loads(receivedData)
    # playerColor = tuple(jsonData["color"])

    print("Playing as color: ", playerColor)

    updateClientThread = threading.Thread(target=clientUpdate)
    updateClientThread.start()

pygame.init()

# Create the window
screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))


# Create a surface for drawing
drawingSurface = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE))
drawingSurface.fill(WHITE)  # Fill with white initially

# Variables to keep track of the cell being colored
coloring = False
currentCell = None

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            gridX, gridY = x // CELL_SIZE, y // CELL_SIZE
            currentCell = (gridX, gridY)
            
            if gridLocks[gridY][gridX] == None:
                coloring = True
        elif event.type == pygame.MOUSEBUTTONUP:
            coloring = False
            
            # Calculate the percentage of the cell that is colored
            cellSurface = pygame.Surface((CELL_SIZE, CELL_SIZE))
            cell_rect = pygame.Rect(currentCell[0]*CELL_SIZE, currentCell[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            cellSurface.blit(drawingSurface, (0, 0), area=cell_rect)
            coloredPixels = pygame.mask.from_threshold(cellSurface, playerColor, (10,10,10)).count()
            totalPixels = CELL_SIZE * CELL_SIZE

            # Sets the cell to be filled and transmits this data to all players
            if coloredPixels / totalPixels >= 0.5:
                grid[currentCell[1]][currentCell[0]] = playerColor
                
                cellCoords = (currentCell[0], currentCell[1])
                jsonFillData = json.dumps({"type": "fill", "color": playerColor, "coords": cellCoords})
                # jsonLockData = json.dumps({"type": "lock", "coords": cellCoords})

                if (isServer):
                    broadcast(jsonFillData)
                    # broadcast(jsonLockData)
                else:
                    clientSocket.send(jsonFillData.encode('utf-8'))
                    # clientSocket.send(jsonLockData.encode('utf-8'))

            # Clear the entire drawing surface
            drawingSurface.fill(WHITE)

    if coloring:
        x, y = pygame.mouse.get_pos()
        pygame.draw.rect(drawingSurface, playerColor, (x-BRUSH_SIZE//2, y-BRUSH_SIZE//2, BRUSH_SIZE, BRUSH_SIZE))

    # Draw the grid
    screen.fill(BLACK)  # Fill the screen with black to create grid lines
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            pygame.draw.rect(screen, grid[y][x], (x*CELL_SIZE + BORDER_SIZE, y*CELL_SIZE + BORDER_SIZE, CELL_SIZE - 2*BORDER_SIZE, CELL_SIZE - 2*BORDER_SIZE))

    # Draw the drawing surface onto the screen
    screen.blit(drawingSurface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)  # Use a blend mode to prevent covering grid lines

    pygame.display.flip()

clientSocket.close()
serverSocket.close()

pygame.quit()
