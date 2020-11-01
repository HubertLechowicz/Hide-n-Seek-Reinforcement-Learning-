from game_env.hidenseek_gym.config import config as default_config
from game_env.hidenseek_gym.controllable import Seeker, Hiding
from game_env.hidenseek_gym.fixed import Wall

import copy
import math


class Helpers:
    @staticmethod
    def change_config_value_type(default_config, tree):
        """
        Checks every item type in Default Config
        > If not `dict` then casts Platform Config item to given type
        > If `dict`, runs recursively for as long as there is other nested `dict`

        Returns new Platform config with proper item types
        """

        for k, v in tree.items():
            if isinstance(default_config[k], bool):
                tree[k] = True if v else False
            elif isinstance(default_config[k], float):
                tree[k] = float(v)
            elif isinstance(default_config[k], int):
                tree[k] = int(v)
            elif isinstance(default_config[k], dict):
                tree[k] = Helpers.change_config_value_type(
                    default_config[k], tree[k])

        return tree

    @staticmethod
    def prepare_config(config_data):
        # https://stackoverflow.com/a/35508197
        tree = {}
        for key, val in config_data.items():
            t = tree
            prev = None
            for part in key.split("-"):
                if prev is not None:
                    t = t.setdefault(prev, {})
                prev = part
            else:
                t.setdefault(prev, val)

        # checkboxes
        tree['game']['reverse'] = True if 'game-reverse' in config_data else False
        tree['video']['draw_pov'] = True if 'video-draw_pov' in config_data else False
        tree['video']['monitoring'] = True if 'video-monitoring' in config_data else False

        # concat dictionaries, with second being more important (take type from first)
        tree = Helpers.change_config_value_type(default_config, tree)

        new_cfg = {**default_config, **tree}

        return new_cfg

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
                wall_direction = math.pi / 2 if obj_width > obj_height else 0
                walls_group.append(
                    Wall(None, center_x, center_y, obj_size, wall_direction))

            elif obj["type"] == "seeker":
                player_seek = Seeker(cfg['seeker'], obj_size, (center_x, center_y), (
                    255, 255, 255), width, height, (255, 255, 0))

            elif obj["type"] == "hider":
                player_hide = Hiding(cfg['hiding'], obj_size, (center_x, center_y), (
                    255, 0, 0), width, height)

        return walls_group, player_seek, player_hide, width, height
