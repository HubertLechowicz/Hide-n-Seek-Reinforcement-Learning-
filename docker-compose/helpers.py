from game_env.hidenseek_gym.config import config as default_config
from game_env.hidenseek_gym.controllable import Seeker, Hiding
from game_env.hidenseek_gym.fixed import Wall

import copy


class Helpers:
    @staticmethod
    def prepare_config(config_data):
        cfg = copy.deepcopy(default_config)
        if '.bmp' not in config_data['map_path']:
            config_data['map_path'] += '.bmp'

        cfg['GAME']['MAP'] = '/opt/app/' + config_data['map_path']
        cfg['GAME']['FPS'] = config_data['fps']
        cfg['GAME']['DURATION'] = config_data['duration']
        cfg['GAME']['DRAW_POV'] = config_data['draw_pov']
        episodes = int(config_data['episodes'])

        cfg['AGENT_HIDING'] = {
            'SPEED_RATIO': config_data['hiding-speed'],
            'SPEED_ROTATE_RATIO': config_data['hiding-speed-rotate'],
            'WALL_ACTION_TIMEOUT': config_data['hiding-wall-timeout'],
            'WALLS_MAX': config_data['hiding-walls'],
        }

        cfg['AGENT_SEEKER'] = {
            'SPEED_RATIO': config_data['seeker-speed'],
            'SPEED_ROTATE_RATIO': config_data['seeker-speed-rotate'],
            'WALL_ACTION_TIMEOUT': config_data['seeker-wall-timeout'],
        }

        return cfg, episodes

    @staticmethod
    def generate_map(all_objects, map_bmp, cfg):
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
                walls_group.append(
                    Wall(None, center_x, center_y, obj_size))

            elif obj["type"] == "seeker":
                player_seek = Seeker(cfg['AGENT_SEEKER'], obj_size, (center_x, center_y), (
                    255, 255, 255), width, height, (255, 255, 0))

            elif obj["type"] == "hider":
                player_hide = Hiding(cfg['AGENT_HIDING'], obj_size, (center_x, center_y), (
                    255, 0, 0), width, height)

        return walls_group, player_seek, player_hide, width, height
