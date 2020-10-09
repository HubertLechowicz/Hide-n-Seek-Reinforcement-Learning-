import pygame
import sys
import os
import logging

from ext.engine import HideNSeek
from ext.loggers import setup_logger, LOGGING_DASHES, logger_engine
from ext.config import config

if __name__ == "__main__":
    logger_engine.info(f"{LOGGING_DASHES} Initializing game {LOGGING_DASHES}")
    os.environ['SDL_VIDEO_CENTERED'] = config['VIDEO']['CENTERED']
    render_mode = 'human'

    pygame.init()
    game = HideNSeek(config=config)
    game.init()
    game.render(render_mode)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger_engine.info(
                    f"{LOGGING_DASHES} Game exited by user {LOGGING_DASHES}")
                pygame.quit()
                sys.exit()
        game.step()

        gameover, winner = game.game_over()
        if gameover:
            logger_engine.info(
                f"{LOGGING_DASHES} Game over with result: {winner} {LOGGING_DASHES}")
            game.render(close=True)
            sys.exit()

        game.render(render_mode)
