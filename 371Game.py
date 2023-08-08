import socket
import threading
import pygame
import numpy as np
import json

# Constants
SERVER_IP = '172.29.179.39'
PORT = 12345

CELL_SIZE = 50
GRID_SIZE = 8
SCREEN_SIZE = GRID_SIZE * CELL_SIZE

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)

BORDER_SIZE = 2
BRUSH_SIZE = 10

# These colors will be assigned to the clients (players) that connect to the server
PLAYER_COLORS = [BLUE, GREEN, YELLOW, CYAN]

# server host will take the default red color
playerColor = RED

# global variables
sockets = []
grid = np.full((GRID_SIZE, GRID_SIZE, 3), WHITE, dtype=int)
gridLocks = np.full((GRID_SIZE, GRID_SIZE), None, dtype=object)

runThreads = True
activeThreads = []

def findWinner():
    # all colors in PLAYER_COLOURS
    colorCounts = {(255, 0, 0): 0, (0, 0, 255): 0, (0, 255, 0): 0, (255, 255, 0): 0, (0, 255, 255): 0}
    for row in grid:
        for color in row:
            if tuple(color) in colorCounts:
                colorCounts[tuple(color)] += 1

    # Get the color with the most cells
    winner_color = max(colorCounts, key=colorCounts.get)

    if winner_color == playerColor:
        print("You win!")
    else:
        print("You lose!")

def broadcast(data):
    for client in sockets:
        try:
            client.send(data.encode('utf-8'))
        except:
            # If sending fails, client has disconnected
            print("BROADCAST FAILED")
            client.close()
            sockets.remove(client)

def processData(data):
    global playerColor
    global gridLocks
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
        gridLocks[y][x] = tuple(data["color"])


def clientHandler(clientSocket):
    global runThreads
    while runThreads:
        try:
            if clientSocket not in sockets:
                break
            
            receivedData = clientSocket.recv(1024).decode('utf-8')
            
            # if receivedData is empty, it means the client has disconnected
            if not receivedData:
                break
            broadcast(receivedData)
            processData(receivedData)

        except socket.timeout:
            continue

def clientUpdate():
    global runThreads
    while runThreads:
        try:
            receivedData = clientSocket.recv(1024).decode('utf-8')
            if not receivedData:
                break
            processData(receivedData)

        except Exception as e:
            print(f"Error updating client: {e}")
            clientSocket.close()
            break

isServer = False
serverSocket = None
clientSocket = None

# Starts server if not already started
try:
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind((SERVER_IP, PORT))
    print("Server is waiting for connections...")
    serverSocket.listen()
    isServer = True
# clients join if a host already exists
except:
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((SERVER_IP, PORT))
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
    while len(sockets) < playerCount - 1:
        clientSocket, address = serverSocket.accept()

        colorData = json.dumps({"type": "setColor", "color": PLAYER_COLORS[len(sockets)]})
        clientSocket.send(colorData.encode("utf-8"))

        sockets.append(clientSocket)
        clientThread = threading.Thread(target=clientHandler, args=(clientSocket,))
        activeThreads.append(clientThread)
        clientThread.start()
        print(f"Connection {len(sockets)} established")
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
    activeThreads.append(updateClientThread)
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
            
            print("grid lock: ", gridLocks[gridY][gridX])
            print("playerColor: ", playerColor)
            if gridLocks[gridY][gridX] == None or gridLocks[gridY][gridX] == playerColor:
                coloring = True
                # Lock the cell with the current player's color
                gridLocks[gridY][gridX] = playerColor
                
                # Notify other players about the lock
                cellCoords = (gridX, gridY)
                jsonLockData = json.dumps({"type": "lock", "color": playerColor, "coords": cellCoords})
                if (isServer):
                    broadcast(jsonLockData)
                else:
                    clientSocket.send(jsonLockData.encode('utf-8'))

        elif event.type == pygame.MOUSEBUTTONUP:
            coloring = False
            
            # Calculate the percentage of the cell that is colored
            cellSurface = pygame.Surface((CELL_SIZE, CELL_SIZE))
            left = currentCell[0]*CELL_SIZE
            top = currentCell[1]*CELL_SIZE
            cellBox = pygame.Rect(left, top, CELL_SIZE, CELL_SIZE)
            cellSurface.blit(drawingSurface, (0, 0), area=cellBox)
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
                else:
                    clientSocket.send(jsonFillData.encode('utf-8'))

            elif gridLocks[currentCell[1]][currentCell[0]] != 1:
                gridLocks[currentCell[1]][currentCell[0]] = None

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

    isAllFilled = all(cell == 1 for row in gridLocks for cell in row)

    if isAllFilled:
        findWinner()
        runThreads = False
        running = False
        break

# For the server
if isServer:
    # And then finally close the sockets:
    for client in sockets:
        client.shutdown(socket.SHUT_RDWR)
        client.close()

# For the client
else:
    updateClientThread.join()
    if clientSocket:
        clientSocket.close()

# Ensure threads are all joined before exiting program
runThreads = False
for thread in activeThreads:
    thread.join()

pygame.quit()
