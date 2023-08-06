import pygame
import numpy as np

# Initialize Pygame
pygame.init()

# define constants
CELL_SIZE = 50
GRID_SIZE = 8
SCREEN_SIZE = GRID_SIZE * CELL_SIZE
PLAYER_COLOR = (255, 0, 0)  # Player's color is red
WHITE = (255, 255, 255)  # Unclaimed cells are white
BLACK = (0, 0, 0)  # Cell border is black
BORDER_SIZE = 2  # Size of the cell border
BRUSH_SIZE = 5  # Size of the brush

# Create the window
screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE))

# Create a grid to track the cell colors
grid = np.full((GRID_SIZE, GRID_SIZE, 3), WHITE, dtype=int)

# Create a surface for drawing
drawing_surface = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE))
drawing_surface.fill(WHITE)  # Fill with white initially

# Variables to keep track of the cell being colored
coloring = False
current_cell = None

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            grid_x, grid_y = x // CELL_SIZE, y // CELL_SIZE
            current_cell = (grid_x, grid_y)
            coloring = True
        elif event.type == pygame.MOUSEBUTTONUP:
            coloring = False
            # Calculate the percentage of the cell that is colored
            cell_surface = pygame.Surface((CELL_SIZE, CELL_SIZE))
            cell_rect = pygame.Rect(current_cell[0]*CELL_SIZE, current_cell[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            cell_surface.blit(drawing_surface, (0, 0), area=cell_rect)
            colored_pixels = pygame.mask.from_threshold(cell_surface, PLAYER_COLOR, (10,10,10)).count()
            total_pixels = CELL_SIZE * CELL_SIZE
            if colored_pixels / total_pixels >= 0.5:
                grid[current_cell[1]][current_cell[0]] = PLAYER_COLOR
            # Clear the entire drawing surface
            drawing_surface.fill(WHITE)

    if coloring:
        x, y = pygame.mouse.get_pos()
        pygame.draw.rect(drawing_surface, PLAYER_COLOR, (x-BRUSH_SIZE//2, y-BRUSH_SIZE//2, BRUSH_SIZE, BRUSH_SIZE))

    # Draw the grid
    screen.fill(BLACK)  # Fill the screen with black to create grid lines
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            pygame.draw.rect(screen, grid[y][x], (x*CELL_SIZE + BORDER_SIZE, y*CELL_SIZE + BORDER_SIZE, CELL_SIZE - 2*BORDER_SIZE, CELL_SIZE - 2*BORDER_SIZE))

    # Draw the drawing surface onto the screen
    screen.blit(drawing_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)  # Use a blend mode to prevent covering grid lines

    pygame.display.flip()

pygame.quit()
