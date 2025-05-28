# Draw quantum goal probability clouds or collapsed state
if quantum_goal:
    quantum_goal.draw(screen)
    import pygame
import sys
import os
import json
import random
import math
import time

# Game configuration
TILE_SIZE = 32
GRID_WIDTH = 20
GRID_HEIGHT = 16
SCREEN_WIDTH = TILE_SIZE * GRID_WIDTH
SCREEN_HEIGHT = TILE_SIZE * GRID_HEIGHT
FPS = 60

# Color palette
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (200, 200, 200)
MOVABLE_COLOR = (200, 100, 100)
ENTANGLABLE_COLOR = (240, 160, 80)
PLAYER_COLOR = (100, 200, 100)
UNMOVABLE_COLOR = (100, 100, 200)
BOX_COLOR = (200, 200, 50)
GOAL_COLOR = (50, 200, 200)
SUPERPOSITION_COLOR = (150, 0, 255)
PLAYER_BLOCKED_COLOR = (150, 150, 150)

# Track selected box for entanglement
selected_box = None


class Entity:
    """Base class for all game objects"""

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color

    def draw(self, surface):
        rect = pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, self.color, rect)

    def can_move(self):
        return False


class MovableBlock(Entity):
    """Block that can be pushed around, optionally entanglable"""

    def __init__(self, x, y, entanglable=False):
        super().__init__(x, y, MOVABLE_COLOR)
        self.entanglable = entanglable
        self.entangled_with = None
        self.selected = False
        if self.entanglable:
            self.color = ENTANGLABLE_COLOR

    def can_move(self):
        return True

    def draw(self, surface):
        super().draw(surface)
        # Add white border for entanglable blocks
        if self.entanglable:
            rect = pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(surface, WHITE, rect, 2)
        # Red highlight for selected blocks
        if self.selected:
            rect = pygame.Rect(self.x * TILE_SIZE + 2, self.y * TILE_SIZE + 2, TILE_SIZE - 4, TILE_SIZE - 4)
            pygame.draw.rect(surface, (255, 0, 0), rect, 3)


class UnmovableTile(Entity):
    """Solid wall that blocks all movement"""

    def __init__(self, x, y):
        super().__init__(x, y, UNMOVABLE_COLOR)


class PlayerBlockedTile(Entity):
    """Special tile that only blocks the player, not other entities"""

    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_BLOCKED_COLOR)


class SuperpositionWall(Entity):
    """Quantum wall that exists in superposition until observed"""

    def __init__(self, x, y, collapse_probability=None):
        if collapse_probability is None:
            collapse_probability = random.random()
        super().__init__(x, y, SUPERPOSITION_COLOR)
        self.is_superposition = True
        self.collapse_probability = collapse_probability
        self.shimmer_offset = random.random() * math.pi * 2
        self.creation_time = time.time()

    def draw(self, surface):
        if self.is_superposition:
            # Create shimmering quantum effect
            current_time = time.time()
            shimmer = math.sin((current_time - self.creation_time) * 4 + self.shimmer_offset)
            base_alpha = int(50 + 30 * shimmer)
            alpha_variation = int(base_alpha * self.collapse_probability)
            color_variation = int(100 + 50 * shimmer * self.collapse_probability)

            shimmer_color = (
                min(255, 150 + color_variation),
                min(255, int(50 + 30 * shimmer * self.collapse_probability)),
                255
            )

            rect = pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            temp_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            temp_surface.set_alpha(alpha_variation + 50)
            temp_surface.fill(shimmer_color)
            surface.blit(temp_surface, (self.x * TILE_SIZE, self.y * TILE_SIZE))

            # Add sparkle effects based on collapse probability
            max_sparkles = 10
            sparkle_count = int(self.collapse_probability * max_sparkles)
            for _ in range(sparkle_count):
                sparkle_x = self.x * TILE_SIZE + random.randint(4, TILE_SIZE - 4)
                sparkle_y = self.y * TILE_SIZE + random.randint(4, TILE_SIZE - 4)
                pygame.draw.circle(surface, (255, 255, 255), (sparkle_x, sparkle_y), 1)
        else:
            super().draw(surface)

    def collapse_wavefunction(self):
        """Collapse from superposition to solid or empty"""
        if not self.is_superposition:
            return self.can_block()

        self.is_superposition = False
        if random.random() < self.collapse_probability:
            self.color = UNMOVABLE_COLOR
            self._is_solid = True
        else:
            self._is_solid = False
        return self._is_solid

    def can_block(self):
        if self.is_superposition:
            return True
        return getattr(self, '_is_solid', True)


class SchrodingerBox(MovableBlock):
    """Special box for the Sokoban puzzle"""

    def __init__(self, x, y):
        super().__init__(x, y)
        self.color = BOX_COLOR


class Goal(Entity):
    """Target location for boxes"""

    def __init__(self, x, y):
        super().__init__(x, y, GOAL_COLOR)


class Player(Entity):
    """The player character"""

    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_COLOR)

    def move(self, dx, dy, grid):
        """Attempt to move in the given direction"""
        target_x, target_y = self.x + dx, self.y + dy

        if not grid.in_bounds(target_x, target_y):
            return

        # Check what's at the target position
        entities = grid.get_entities(target_x, target_y)

        # Collapse any superposition walls
        for entity in entities[:]:
            if isinstance(entity, SuperpositionWall):
                is_solid = entity.collapse_wavefunction()
                if not is_solid:
                    grid.remove_entity(entity)
                    entities.remove(entity)

        # Check for blocking entities (player can't pass through player-blocked tiles)
        blocking_entities = []
        for e in entities:
            if isinstance(e, PlayerBlockedTile):
                return  # Player can't move here
            elif not isinstance(e, Goal) and (not isinstance(e, SuperpositionWall) or e.can_block()):
                blocking_entities.append(e)

        if not blocking_entities:
            grid.move_entity(self, target_x, target_y)
        else:
            # Try to push the first blocking entity
            first_blocker = blocking_entities[0]
            if first_blocker.can_move() and grid.push(first_blocker, dx, dy):
                grid.move_entity(self, target_x, target_y)


def handle_entangle_click(grid, gx, gy):
    """Handle clicking on blocks to create quantum entanglement"""
    global selected_box

    for entity in grid.get_entities(gx, gy):
        if isinstance(entity, MovableBlock) and entity.entanglable:
            # Break existing entanglement
            if entity.entangled_with:
                partner = entity.entangled_with
                entity.entangled_with = None
                partner.entangled_with = None
                return

            # Deselect if clicking the same box
            if selected_box is entity:
                entity.selected = False
                selected_box = None
                return

            # Select first box
            if selected_box is None:
                selected_box = entity
                entity.selected = True
                return

            # Create entanglement between boxes
            if entity is not selected_box:
                selected_box.entangled_with = entity
                entity.entangled_with = selected_box

            selected_box.selected = False
            selected_box = None
            return


class Grid:
    """Game grid that manages entity positions"""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cells = [[[] for _ in range(height)] for _ in range(width)]

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def add_entity(self, entity):
        self.cells[entity.x][entity.y].append(entity)

    def remove_entity(self, entity):
        if entity in self.cells[entity.x][entity.y]:
            self.cells[entity.x][entity.y].remove(entity)

    def move_entity(self, entity, x, y):
        self.remove_entity(entity)
        entity.x = x
        entity.y = y
        self.add_entity(entity)

    def get_entities(self, x, y):
        return list(self.cells[x][y])

    def _handle_entanglement(self, entity, dx, dy):
        """Move entangled partner when entity moves"""
        if hasattr(entity, 'entangled_with') and entity.entangled_with:
            partner = entity.entangled_with
            new_x, new_y = partner.x + dx, partner.y + dy
            if self.in_bounds(new_x, new_y):
                self.move_entity(partner, new_x, new_y)

    def push(self, entity, dx, dy):
        """Attempt to push an entity in the given direction"""
        new_x, new_y = entity.x + dx, entity.y + dy

        if not self.in_bounds(new_x, new_y):
            return False

        entities = self.get_entities(new_x, new_y)

        # Collapse superposition walls
        for ent in entities[:]:
            if isinstance(ent, SuperpositionWall):
                is_solid = ent.collapse_wavefunction()
                if not is_solid:
                    self.remove_entity(ent)
                    entities.remove(ent)

        # Find blocking entities (exclude goals and player-blocked tiles)
        blocking_entities = []
        for ent in entities:
            if (not isinstance(ent, Goal) and
                    not isinstance(ent, PlayerBlockedTile) and
                    (not isinstance(ent, SuperpositionWall) or ent.can_block())):
                blocking_entities.append(ent)

        # Can move to position with goal
        if any(isinstance(e, Goal) for e in entities) and not blocking_entities:
            self.move_entity(entity, new_x, new_y)
            self._handle_entanglement(entity, dx, dy)
            return True

        # Can move to empty space
        if not blocking_entities:
            self.move_entity(entity, new_x, new_y)
            self._handle_entanglement(entity, dx, dy)
            return True

        # Try to push the blocking entity
        first_blocker = blocking_entities[0]
        if first_blocker.can_move() and self.push(first_blocker, dx, dy):
            self.move_entity(entity, new_x, new_y)
            self._handle_entanglement(entity, dx, dy)
            return True

        return False


def load_level(grid, layout):
    """Load level layout into the grid"""
    # Character to entity mapping
    entity_map = {
        '#': lambda x, y: UnmovableTile(x, y),
        'P': lambda x, y: Player(x, y),
        'B': lambda x, y: SchrodingerBox(x, y),
        'X': lambda x, y: Goal(x, y),
        'M': lambda x, y: MovableBlock(x, y, entanglable=False),
        'E': lambda x, y: MovableBlock(x, y, entanglable=True),
        'Q': lambda x, y: SuperpositionWall(x, y),
        'T': lambda x, y: PlayerBlockedTile(x, y),
    }

    for y, row in enumerate(layout):
        for x, char in enumerate(row):
            if char in entity_map:
                grid.add_entity(entity_map[char](x, y))


def wrap_text(text, font, max_width):
    """Break text into lines that fit within the given width"""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        text_width = font.size(test_line)[0]

        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                lines.append(word)

    if current_line:
        lines.append(' '.join(current_line))

    return lines


def show_level_intro(screen, clock, level_data, level_number):
    """Display level introduction with fade-in animation"""
    font_title = pygame.font.Font(None, 48)
    font_desc = pygame.font.Font(None, 28)
    font_continue = pygame.font.Font(None, 24)

    level_name = level_data.get('name', f'Level {level_number + 1}')
    level_description = level_data.get('description', 'No description available.')

    start_time = time.time()
    fade_duration = 1.0
    waiting_for_input = False

    while True:
        current_time = time.time()
        elapsed = current_time - start_time

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                if waiting_for_input:
                    return True

        # Calculate fade-in alpha
        if elapsed < fade_duration:
            alpha = int(255 * (elapsed / fade_duration))
        else:
            alpha = 255
            waiting_for_input = True

        # Clear screen
        screen.fill(DARK_GRAY)

        # Render title with fade effect
        title_surface = font_title.render(level_name, True, WHITE)
        title_surface.set_alpha(alpha)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        screen.blit(title_surface, title_rect)

        # Render wrapped description
        max_desc_width = SCREEN_WIDTH - 100
        desc_lines = wrap_text(level_description, font_desc, max_desc_width)
        desc_start_y = title_rect.bottom + 40
        line_height = font_desc.get_height() + 5

        for i, line in enumerate(desc_lines):
            desc_surface = font_desc.render(line, True, LIGHT_GRAY)
            desc_surface.set_alpha(alpha)
            desc_rect = desc_surface.get_rect(center=(SCREEN_WIDTH // 2, desc_start_y + i * line_height))
            screen.blit(desc_surface, desc_rect)

        # Show pulsing continue prompt
        if waiting_for_input:
            pulse = math.sin(current_time * 3) * 0.3 + 0.7
            continue_alpha = int(255 * pulse)

            continue_text = "Press any key or click to continue..."
            continue_surface = font_continue.render(continue_text, True, WHITE)
            continue_surface.set_alpha(continue_alpha)
            continue_rect = continue_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
            screen.blit(continue_surface, continue_rect)

        pygame.display.flip()
        clock.tick(FPS)


def run_levels(level_files):
    """Main game loop"""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Quantum Sokoban - Superposition Mechanics")
    clock = pygame.time.Clock()

    # Load all level data
    all_levels = []
    for filename in level_files:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_levels.append(data)

    def create_level(index):
        """Initialize a level from layout data"""
        grid = Grid(GRID_WIDTH, GRID_HEIGHT)
        load_level(grid, all_levels[index].get('layout', []))
        return grid

    current_level = 0

    # Show intro for first level
    if not show_level_intro(screen, clock, all_levels[current_level], current_level):
        pygame.quit()
        return

    grid = create_level(current_level)

    def check_victory(grid):
        """Check if all boxes are on goals"""
        for x in range(grid.width):
            for y in range(grid.height):
                entities = grid.get_entities(x, y)
                has_box = any(isinstance(e, SchrodingerBox) for e in entities)
                has_goal = any(isinstance(e, Goal) for e in entities)
                if has_box and has_goal:
                    return True
        return False

    running = True
    font = pygame.font.Font(None, 24)

    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x, grid_y = mouse_x // TILE_SIZE, mouse_y // TILE_SIZE
                if grid.in_bounds(grid_x, grid_y):
                    handle_entangle_click(grid, grid_x, grid_y)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_r:
                    # Reset current level
                    grid = create_level(current_level)
                    selected_box = None

                else:
                    # Handle player movement
                    for x in range(GRID_WIDTH):
                        for y in range(GRID_HEIGHT):
                            for entity in grid.get_entities(x, y):
                                if isinstance(entity, Player):
                                    if event.key == pygame.K_UP:
                                        entity.move(0, -1, grid)
                                    elif event.key == pygame.K_DOWN:
                                        entity.move(0, 1, grid)
                                    elif event.key == pygame.K_LEFT:
                                        entity.move(-1, 0, grid)
                                    elif event.key == pygame.K_RIGHT:
                                        entity.move(1, 0, grid)

        # Render everything
        screen.fill(BLACK)

        # Draw grid lines
        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(screen, WHITE, (x * TILE_SIZE, 0), (x * TILE_SIZE, SCREEN_HEIGHT))
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(screen, WHITE, (0, y * TILE_SIZE), (SCREEN_WIDTH, y * TILE_SIZE))

        # Draw all entities
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                for entity in grid.get_entities(x, y):
                    entity.draw(screen)

        # Draw quantum goal probability clouds or collapsed state
        if quantum_goal:
            quantum_goal.draw(screen)

        # Draw entanglement connections
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                for entity in grid.get_entities(x, y):
                    if isinstance(entity, MovableBlock) and getattr(entity, 'selected', False):
                        pygame.draw.rect(screen, (255, 0, 0),
                                         (entity.x * TILE_SIZE, entity.y * TILE_SIZE, TILE_SIZE, TILE_SIZE), 3)

                    if isinstance(entity, MovableBlock) and entity.entangled_with:
                        partner = entity.entangled_with
                        start_pos = (entity.x * TILE_SIZE + TILE_SIZE // 2, entity.y * TILE_SIZE + TILE_SIZE // 2)
                        end_pos = (partner.x * TILE_SIZE + TILE_SIZE // 2, partner.y * TILE_SIZE + TILE_SIZE // 2)
                        pygame.draw.line(screen, (255, 0, 0), start_pos, end_pos, 2)

        # Draw control instructions
        instructions = [
            "Arrow Keys: Move",
            "Click: Entangle blocks (E)",
            "R: Reset level",
            "Purple walls: Quantum superposition",
            "Walk into them to collapse!"
        ]

        for i, instruction in enumerate(instructions):
            text = font.render(instruction, True, WHITE)
            screen.blit(text, (10, SCREEN_HEIGHT - 140 + i * 20))

        pygame.display.flip()
        clock.tick(FPS)

        # Check for level completion
        if check_victory(grid):
            current_level += 1
            if current_level < len(all_levels):
                # Show next level intro
                if not show_level_intro(screen, clock, all_levels[current_level], current_level):
                    running = False
                    break

                grid = create_level(current_level)
                selected_box = None
            else:
                running = False

    pygame.quit()