import pygame
import sys
import os
import logging
from ext.engine import HideNSeek
from ext.loggers import setup_logger, LOGGING_DASHES, logger_engine
from ext.config import config
from ext.supportive import Point, Collision, MapGenerator
from objects.controllable import Seeker, Hiding
from objects.fixed import Wall



def generate_map(all_objects, map_bmp):
    """
    Generates map by using BMP File

    Parameters
    ----------
        all_objects : dict
            dictionary of objects to add into the game

    Returns
    -------
        walls_group : list
            list of wall objects
        player_seek : Object
            Seeker object.
        player_hide : Object
            Hiding object.
        width : int
            game screen width.
        height : int
             game screen int.
    """

    walls_group = []
    player_seek = None
    player_hide = None
    width, height = map_bmp.size

    for obj in all_objects:
        center_x = (obj["vertices"][0]["x"] + obj["vertices"][1]["x"]) / 2
        center_y = (obj["vertices"][0]["y"] + obj["vertices"][1]["y"]) / 2

        obj_width = obj["vertices"][1]["x"] - obj["vertices"][0]["x"]
        obj_height = obj["vertices"][1]["y"] - obj["vertices"][0]["y"]
        obj_size = (obj_width, obj_height)

        if obj["type"] == "wall":
            logger_engine.info("\t\tWall")
            walls_group.append(
                Wall(None, center_x, center_y, obj_size))

        elif obj["type"] == "seeker":
            logger_engine.info("\t\tSeeker Agent")
            player_seek = Seeker(config['AGENT_SEEKER'], obj_size, (center_x, center_y), (
                255, 255, 255), width, height, (255, 255, 0))

        elif obj["type"] == "hider":
            logger_engine.info("\t\tHiding Agent")
            player_hide = Hiding(config['AGENT_HIDING'], obj_size, (center_x, center_y), (
                255, 0, 0), width, height)

    return walls_group, player_seek, player_hide, width, height
if __name__ == "__main__":
    logger_engine.info(f"{LOGGING_DASHES} Initializing game {LOGGING_DASHES}")
    os.environ['SDL_VIDEO_CENTERED'] = config['VIDEO']['CENTERED']
    render_mode = 'human'

    logger_engine.info(f"\tGenerating map from BMP ({config['GAME'].get('MAP_PATH', fallback='maps/map')}.bmp)")
    map_bmp = MapGenerator.open_bmp(config['GAME'].get(
        'MAP_PATH', fallback='maps/map') + '.bmp')
    all_objects = MapGenerator.get_objects_coordinates(
        map_bmp, MapGenerator.get_predefined_palette())

    walls, seeker, hider, width, height = generate_map(all_objects, map_bmp)
    pygame.init()
    game = HideNSeek(config=config)
    game.init(walls, seeker, hider, width, height)
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
