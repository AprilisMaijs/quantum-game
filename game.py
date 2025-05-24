"""
Simple Baba Is You–Style Puzzle Game

Dependencies:
  - Python 3.x
  - pygame (install via `pip install pygame`)

Run:
  `python baba_game.py`
"""

import pygame
import sys
import os
import glob
import json

# Configuration
TILE_SIZE = 32        # smaller tiles
GRID_WIDTH = 20       # double the original width
GRID_HEIGHT = 16      # double the original height
SCREEN_WIDTH = TILE_SIZE * GRID_WIDTH
SCREEN_HEIGHT = TILE_SIZE * GRID_HEIGHT
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
MOVABLE_COLOR = (200, 100, 100)
PLAYER_COLOR = (100, 200, 100)
UNMOVABLE_COLOR = (100, 100, 200)
BOX_COLOR = (200, 200, 50)
GOAL_COLOR = (50, 200, 200)

# Base Entity class
class Entity:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

    def draw(self, surface):
        rect = pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, self.color, rect)

    def can_move(self):
        return False

# Movable block
class MovableBlock(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, MOVABLE_COLOR)

    def can_move(self):
        return True

# Unmovable tile
class UnmovableTile(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, UNMOVABLE_COLOR)

# Special Schrödinger's Box (movable)
class SchrodingerBox(MovableBlock):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = BOX_COLOR

# Goal tile
class Goal(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, GOAL_COLOR)

# Player
class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_COLOR)

    def move(self, dx, dy, grid):
        target_x, target_y = self.x + dx, self.y + dy
        if not grid.in_bounds(target_x, target_y): return
        occupants = grid.get_entities(target_x, target_y)
        # allow stepping on goals
        if not occupants or any(isinstance(o, Goal) for o in occupants):
            grid.move_entity(self, target_x, target_y)
        else:
            first = occupants[0]
            if first.can_move() and grid.push(first, dx, dy):
                grid.move_entity(self, target_x, target_y)

# Grid manager
class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cells = [[[] for _ in range(height)] for _ in range(width)]

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def add_entity(self, entity):
        self.cells[entity.x][entity.y].append(entity)

    def remove_entity(self, entity):
        self.cells[entity.x][entity.y].remove(entity)

    def move_entity(self, entity, x, y):
        self.remove_entity(entity)
        entity.x, entity.y = x, y
        self.add_entity(entity)

    def get_entities(self, x, y):
        return list(self.cells[x][y])

    def push(self, entity, dx, dy):
        nx, ny = entity.x + dx, entity.y + dy
        if not self.in_bounds(nx, ny): return False
        occupants = self.get_entities(nx, ny)
        # allow pushing onto goal
        if any(isinstance(o, Goal) for o in occupants):
            self.move_entity(entity, nx, ny)
            return True
        # if empty, simply move
        if not occupants:
            self.move_entity(entity, nx, ny)
            return True
        # try to push chain
        first = occupants[0]
        if first.can_move() and self.push(first, dx, dy):
            self.move_entity(entity, nx, ny)
            return True
        return False

# Level definition helper
def load_level(grid, layout):
    """
    layout: list of strings with characters:
      '#': unmovable tile
      '.': empty
      'P': player
      'B': schrodinger box
      'X': goal
      'M': movable block
    """
    mapping = {
        '#': UnmovableTile,
        'P': Player,
        'B': SchrodingerBox,
        'X': Goal,
        'M': MovableBlock,
    }
    for y, row in enumerate(layout):
        for x, ch in enumerate(row):
            if ch in mapping:
                grid.add_entity(mapping[ch](x, y))

# Load all level JSONs
def load_all_levels(path='levels'):
    level_files = sorted(glob.glob(os.path.join(path, '*.json')))
    levels = []
    for fn in level_files:
        with open(fn, 'r') as f:
            data = json.load(f)
            levels.append(data.get('layout', []))
    return levels

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# Load levels and start with the first
all_levels = load_all_levels()
current_level = 0

def start_level(index):
    grid = Grid(GRID_WIDTH, GRID_HEIGHT)
    layout = all_levels[index]
    load_level(grid, layout)
    return grid

grid = start_level(current_level)

# Main game loop
def check_win(grid):
    for x in range(grid.width):
        for y in range(grid.height):
            ents = grid.get_entities(x, y)
            if any(isinstance(e, SchrodingerBox) for e in ents) and any(isinstance(e, Goal) for e in ents):
                return True
    return False

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            for ents in [grid.get_entities(x,y) for x in range(grid.width) for y in range(grid.height)]:
                for e in ents:
                    if isinstance(e, Player):
                        if event.key == pygame.K_UP:
                            e.move(0, -1, grid)
                        elif event.key == pygame.K_DOWN:
                            e.move(0, 1, grid)
                        elif event.key == pygame.K_LEFT:
                            e.move(-1, 0, grid)
                        elif event.key == pygame.K_RIGHT:
                            e.move(1, 0, grid)

    screen.fill(BLACK)
    for x in range(GRID_WIDTH + 1):
        pygame.draw.line(screen, WHITE, (x * TILE_SIZE, 0), (x * TILE_SIZE, SCREEN_HEIGHT))
    for y in range(GRID_HEIGHT + 1):
        pygame.draw.line(screen, WHITE, (0, y * TILE_SIZE), (SCREEN_WIDTH, y * TILE_SIZE))
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            for entity in grid.get_entities(x, y):
                entity.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

    if check_win(grid):
        print(f"Level {current_level+1} complete!")
        current_level += 1
        if current_level < len(all_levels):
            grid = start_level(current_level)
        else:
            print("All levels complete!")
            running = False

pygame.quit()
sys.exit()
