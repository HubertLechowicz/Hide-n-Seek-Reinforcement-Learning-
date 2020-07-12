import pygame
import sys
import os

from ext.engine import HideNSeek


if __name__ == "__main__":
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    fps = 24
    pygame.init()
    players_speed_ratio = { # by how many pixels they should move in every 'movement' action step
        'p_hide': fps,
        'p_seek': fps,
    }

    game = HideNSeek(width=512, height=512, fps=fps, speed_ratio=players_speed_ratio)
    game.setup()
    game.init()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        game.step()
        pygame.display.update()
        
        if game.game_over():
            print("Game over")
            pygame.quit()
            sys.exit()
