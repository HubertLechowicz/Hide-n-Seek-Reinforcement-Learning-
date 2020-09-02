import pygame
import sys
import os
import logging

from ext.engine import HideNSeek
from ext.loggers import setup_logger, LOGGING_DASHES, logger_engine

if __name__ == "__main__":
    logger_engine.info(f"{LOGGING_DASHES} Initializing game {LOGGING_DASHES}")
    os.environ['SDL_VIDEO_CENTERED'] = '1'

    fps = 60
    pygame.init()

    players_speed_ratio = { # by how many pixels they should move in every 'movement' action step
        'p_hide': fps,
        'p_seek': fps,
    }

    game_width = 512
    game_height = 512

    game = HideNSeek(width=game_width, height=game_height, fps=fps, speed_ratio=players_speed_ratio, duration=60)
    game.setup()
    game.init()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger_engine.info(f"{LOGGING_DASHES} Game exited by user {LOGGING_DASHES}")
                pygame.quit()
                sys.exit()
        game.step()
        pygame.display.update()
        
        if game.game_over():
            logger_engine.info(f"{LOGGING_DASHES} Game over with result: ---PLACEHOLDER--- {LOGGING_DASHES}")
            pygame.quit()
            sys.exit()
