import sys
import os
import glob
import pygame

# Import the main game module (game.py should define a `run_levels(level_files)` function)
import game

# Configuration
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 60

# Paths
game.LEVEL_PATH = 'levels'

# Initialize Pygame
ingame = pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Baba Quantum")

# Colors and fonts
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
HIGHLIGHT = (200, 200, 50)

title_font = pygame.font.SysFont(None, 72)
menu_font = pygame.font.SysFont(None, 48)

menu_options = ['Play']

def draw_menu(selected):
    screen.fill(BLACK)
    title_surf = title_font.render('Baba QM', True, WHITE)
    screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, 100))

    option = menu_options[0]
    color = HIGHLIGHT if selected == 0 else WHITE
    surf = menu_font.render(option, True, color)
    screen.blit(surf, (SCREEN_WIDTH//2 - surf.get_width()//2, SCREEN_HEIGHT//2 - surf.get_height()//2))

    pygame.display.flip()


def main_menu():
    selected = 0
    clock = pygame.time.Clock()
    while True:
        draw_menu(selected)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return
        clock.tick(FPS)


def get_level_files(path):
    os.makedirs(path, exist_ok=True)
    return sorted(glob.glob(os.path.join(path, '*.json')))


if __name__ == '__main__':
    # Show only Play menu
    main_menu()

    # Launch default levels
    level_files = get_level_files(game.LEVEL_PATH)
    if level_files:
        game.run_levels(level_files)

    pygame.quit()
    sys.exit()
