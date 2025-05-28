"""
main_menu.py
Standalone launcher for game.py
"""
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
game.CUSTOM_PATH = 'custom_levels'

# Fonts and colors
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Baba Quantum Menu")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
HIGHLIGHT = (200, 200, 50)
title_font = pygame.font.SysFont(None, 72)
menu_font = pygame.font.SysFont(None, 48)

menu_options = ['Play Default Levels', 'Create Level', 'Play Custom Levels']


def draw_menu(selected):
    screen.fill(BLACK)
    title_surf = title_font.render('Baba QM', True, WHITE)
    screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, 50))
    for idx, option in enumerate(menu_options):
        color = HIGHLIGHT if idx == selected else WHITE
        surf = menu_font.render(option, True, color)
        screen.blit(surf, (SCREEN_WIDTH//2 - surf.get_width()//2, 180 + idx*60))
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
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(menu_options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(menu_options)
                elif event.key == pygame.K_RETURN:
                    return selected
        clock.tick(FPS)


def get_level_files(path):
    os.makedirs(path, exist_ok=True)
    return sorted(glob.glob(os.path.join(path, '*.json')))


def launch_editor():
    # Launch external editor script
    os.system(f"python level_editor.py")


if __name__ == '__main__':
    choice = main_menu()
    if choice == 0:
        files = get_level_files(game.LEVEL_PATH)
        if files:
            game.run_levels(files)
    elif choice == 1:
        launch_editor()
    else:
        files = get_level_files(game.CUSTOM_PATH)
        if files:
            game.run_levels(files)
    pygame.quit()
    sys.exit()
