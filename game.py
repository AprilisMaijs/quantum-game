import pygame
import sys
import os
import json
# Constants
TILE_SIZE = 32        # tile size
GRID_WIDTH = 20       # grid dimensions
GRID_HEIGHT = 16
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

# Global selection (entanglement)
selected_box = None

# Entity classes
class Entity:
    def __init__(self, x, y, color):
        self.x, self.y, self.color = x, y, color

    def draw(self, surface):
        rect = pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, self.color, rect)

    def can_move(self):
        return False

class MovableBlock(Entity):
    def __init__(self, x, y, entanglable=False):
        super().__init__(x, y, MOVABLE_COLOR)
        self.entanglable = entanglable
        self.entangled_with = None
        self.selected = False

    def can_move(self):
        return True

class UnmovableTile(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, UNMOVABLE_COLOR)

class SchrodingerBox(MovableBlock):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = BOX_COLOR

class Goal(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, GOAL_COLOR)

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_COLOR)

    def move(self, dx, dy, grid):
        tx, ty = self.x + dx, self.y + dy
        if not grid.in_bounds(tx, ty):
            return
        occ = grid.get_entities(tx, ty)
        if not occ or any(isinstance(o, Goal) for o in occ):
            grid.move_entity(self, tx, ty)
        else:
            first = occ[0]
            if first.can_move() and grid.push(first, dx, dy):
                grid.move_entity(self, tx, ty)

# Grid manager
class Grid:
    def __init__(self, w, h):
        self.width, self.height = w, h
        self.cells = [[[] for _ in range(h)] for _ in range(w)]

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def add_entity(self, e):
        self.cells[e.x][e.y].append(e)

    def remove_entity(self, e):
        self.cells[e.x][e.y].remove(e)

    def move_entity(self, e, x, y):
        self.remove_entity(e)
        e.x, e.y = x, y
        self.add_entity(e)

    def get_entities(self, x, y):
        return list(self.cells[x][y])

    def _handle_entanglement(self, e, dx, dy):
        if hasattr(e, 'entangled_with') and e.entangled_with:
            p = e.entangled_with
            nx, ny = p.x + dx, p.y + dy
            if self.in_bounds(nx, ny):
                self.move_entity(p, nx, ny)

    def push(self, e, dx, dy):
        nx, ny = e.x + dx, e.y + dy
        if not self.in_bounds(nx, ny):
            return False
        occ = self.get_entities(nx, ny)
        if any(isinstance(o, Goal) for o in occ):
            self.move_entity(e, nx, ny)
            self._handle_entanglement(e, dx, dy)
            return True
        if not occ:
            self.move_entity(e, nx, ny)
            self._handle_entanglement(e, dx, dy)
            return True
        first = occ[0]
        if first.can_move() and self.push(first, dx, dy):
            self.move_entity(e, nx, ny)
            self._handle_entanglement(e, dx, dy)
            return True
        return False

# Helpers for level loading

def load_level(grid, layout):
    mapping = {
        '#': lambda x,y: UnmovableTile(x,y),
        'P': lambda x,y: Player(x,y),
        'B': lambda x,y: SchrodingerBox(x,y),
        'X': lambda x,y: Goal(x,y),
        'M': lambda x,y: MovableBlock(x,y, entanglable=False),
        'E': lambda x,y: MovableBlock(x,y, entanglable=True),
    }
    for y, row in enumerate(layout):
        for x, ch in enumerate(row):
            if ch in mapping:
                grid.add_entity(mapping[ch](x, y))

# Main entry for menu integration
def run_levels(level_files):
    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    # Load all layouts
    all_levels = []
    for fn in level_files:
        with open(fn) as f:
            data = json.load(f)
            all_levels.append(data.get('layout', []))

    def start_level(idx):
        g = Grid(GRID_WIDTH, GRID_HEIGHT)
        load_level(g, all_levels[idx])
        return g

    current = 0
    grid = start_level(current)

    def check_win(g):
        for x in range(g.width):
            for y in range(g.height):
                ents = g.get_entities(x, y)
                if any(isinstance(e, SchrodingerBox) for e in ents) and any(isinstance(e, Goal) for e in ents):
                    return True
        return False

    running = True
    global selected_box
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                mx,my = pygame.mouse.get_pos()
                gx,gy = mx//TILE_SIZE, my//TILE_SIZE
                if grid.in_bounds(gx, gy):
                    for o in grid.get_entities(gx, gy):
                        if isinstance(o, MovableBlock) and o.entanglable:
                            if selected_box is None:
                                selected_box = o; o.selected = True
                            else:
                                if o is not selected_box:
                                    selected_box.entangled_with = o
                                    o.entangled_with = selected_box
                                selected_box.selected = False
                                selected_box = None
                            break
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    running = False
                else:
                    for ents in [grid.get_entities(x,y) for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT)]:
                        for e in ents:
                            if isinstance(e, Player):
                                if ev.key == pygame.K_UP:    e.move(0, -1, grid)
                                if ev.key == pygame.K_DOWN:  e.move(0, 1, grid)
                                if ev.key == pygame.K_LEFT:  e.move(-1, 0, grid)
                                if ev.key == pygame.K_RIGHT: e.move(1, 0, grid)

        # Draw
        screen.fill(BLACK)
        for x in range(GRID_WIDTH+1): pygame.draw.line(screen, WHITE, (x*TILE_SIZE,0),(x*TILE_SIZE,SCREEN_HEIGHT))
        for y in range(GRID_HEIGHT+1): pygame.draw.line(screen, WHITE, (0,y*TILE_SIZE),(SCREEN_WIDTH,y*TILE_SIZE))
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                for ent in grid.get_entities(x,y): ent.draw(screen)
        # draw entangle highlights
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                for e in grid.get_entities(x,y):
                    if isinstance(e, MovableBlock) and getattr(e,'selected',False):
                        pygame.draw.rect(screen, (255,0,0), (e.x*TILE_SIZE,e.y*TILE_SIZE,TILE_SIZE,TILE_SIZE),3)
                    if isinstance(e, MovableBlock) and e.entangled_with:
                        p = e.entangled_with
                        start = (e.x*TILE_SIZE+TILE_SIZE//2,e.y*TILE_SIZE+TILE_SIZE//2)
                        end   = (p.x*TILE_SIZE+TILE_SIZE//2,p.y*TILE_SIZE+TILE_SIZE//2)
                        pygame.draw.line(screen,(255,0,0),start,end,2)

        pygame.display.flip()
        clock.tick(FPS)

        if check_win(grid):
            current += 1
            if current < len(all_levels):
                grid = start_level(current)
            else:
                running = False

    pygame.quit()
