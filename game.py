import pygame
import sys

# Configuration
TILE_SIZE = 64
GRID_WIDTH = 10
GRID_HEIGHT = 8
SCREEN_WIDTH = TILE_SIZE * GRID_WIDTH
SCREEN_HEIGHT = TILE_SIZE * GRID_HEIGHT
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Entity base class
class Entity:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

    def draw(self, surface):
        rect = pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, self.color, rect)

    def can_move(self):
        # By default, entities are immovable
        return False

# Movable block
class MovableBlock(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, (200, 100, 100))

    def can_move(self):
        return True

# Player ("You")
class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, (100, 200, 100))

    def move(self, dx, dy, grid):
        target_x = self.x + dx
        target_y = self.y + dy
        if not grid.in_bounds(target_x, target_y):
            return
        occupants = grid.get_entities(target_x, target_y)
        # If no occupants, move
        if not occupants:
            grid.move_entity(self, target_x, target_y)
        else:
            # If first occupant can move, try to push it
            first = occupants[0]
            if first.can_move():
                if grid.push(first, dx, dy):
                    grid.move_entity(self, target_x, target_y)

# Simple grid to manage entities
class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Each cell holds list of entities
        self.cells = [[[] for _ in range(height)] for _ in range(width)]

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def add_entity(self, entity):
        self.cells[entity.x][entity.y].append(entity)

    def remove_entity(self, entity):
        self.cells[entity.x][entity.y].remove(entity)

    def move_entity(self, entity, x, y):
        self.remove_entity(entity)
        entity.x = x
        entity.y = y
        self.add_entity(entity)

    def get_entities(self, x, y):
        return list(self.cells[x][y])

    def push(self, entity, dx, dy):
        target_x = entity.x + dx
        target_y = entity.y + dy
        if not self.in_bounds(target_x, target_y):
            return False
        occupants = self.get_entities(target_x, target_y)
        if not occupants:
            self.move_entity(entity, target_x, target_y)
            return True
        first = occupants[0]
        if first.can_move() and self.push(first, dx, dy):
            self.move_entity(entity, target_x, target_y)
            return True
        return False

# Initialize pygame and game objects
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

grid = Grid(GRID_WIDTH, GRID_HEIGHT)
player = Player(1, 1)
grid.add_entity(player)

# Add some blocks for demo
for bx, by in [(3, 1), (4,1), (5,1)]:
    block = MovableBlock(bx, by)
    grid.add_entity(block)

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_UP:
                player.move(0, -1, grid)
            elif event.key == pygame.K_DOWN:
                player.move(0, 1, grid)
            elif event.key == pygame.K_LEFT:
                player.move(-1, 0, grid)
            elif event.key == pygame.K_RIGHT:
                player.move(1, 0, grid)

    screen.fill(BLACK)
    # Draw grid lines
    for x in range(GRID_WIDTH + 1):
        pygame.draw.line(screen, WHITE, (x * TILE_SIZE, 0), (x * TILE_SIZE, SCREEN_HEIGHT))
    for y in range(GRID_HEIGHT + 1):
        pygame.draw.line(screen, WHITE, (0, y * TILE_SIZE), (SCREEN_WIDTH, y * TILE_SIZE))

    # Draw entities
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            for entity in grid.get_entities(x, y):
                entity.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()

# This basic framework sets up a grid, a player, and movable blocks.
# It's structured with classes so you can easily add new mechanics, including quantum behaviors,
# by extending Entity and Grid methods.
