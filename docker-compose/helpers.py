from game_env.hidenseek_gym.config import config as default_config
from game_env.hidenseek_gym.controllable import Seeker, Hiding
from game_env.hidenseek_gym.fixed import Wall

import math
from PIL import Image as img
from pathlib import Path
import random
import shutil
import statistics

import gym

from game_env.hidenseek_gym import wrappers as multi_wrappers
from game_env.hidenseek_gym.controllable import Seeker, Hiding
from game_env.hidenseek_gym.supportive import Point, MapGenerator
from game_env.hidenseek_gym.fixed import Wall
from rl import A2C, PPO


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
        tree['game']['continuous_reward'] = True if 'game-continuous_reward' in config_data else False
        tree['video']['draw_pov'] = True if 'video-draw_pov' in config_data else False
        tree['video']['monitoring'] = True if 'video-monitoring' in config_data else False

        tree['game']['graphics_path_wall'] = default_config['game']['graphics_path_wall']
        tree['game']['graphics_path_wall_owner'] = default_config['game']['graphics_path_wall_owner']
        tree['seeker']['graphics_path'] = default_config['seeker']['graphics_path']
        tree['hiding']['graphics_path'] = default_config['hiding']['graphics_path']

        # concat dictionaries, with second being more important (take type from first)
        tree = Helpers.change_config_value_type(default_config, tree)

        new_cfg = {**default_config, **tree}

        return new_cfg

    @staticmethod
    def _generate_map(all_objects, map_bmp, cfg):
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
                    Wall(None, center_x, center_y, obj_size, cfg['game']['graphics_path_wall'], wall_direction))

            elif obj["type"] == "seeker":
                player_seek = Seeker(
                    cfg['seeker'], obj_size, (center_x, center_y), width, height)

            elif obj["type"] == "hider":
                player_hide = Hiding(
                    cfg['hiding'], obj_size, (center_x, center_y), width, height)

        return walls_group, player_seek, player_hide, width, height

    @staticmethod
    def prepare_map(cfg):
        map_bmp = MapGenerator.open_bmp(cfg['game']['map'])
        all_objects = MapGenerator.get_objects_coordinates(
            map_bmp, MapGenerator.get_predefined_palette())

        walls, seeker, hider, width, height = Helpers._generate_map(
            all_objects, map_bmp, cfg)

        map_bmp.close()  # memory management

        return walls, seeker, hider, width, height

    @staticmethod
    def pick_algorithm(cfg, **kwargs):
        if cfg['game']['algorithm'] == 'a2c':
            return A2C(
                env=kwargs['env'],
                num_agents=kwargs['agents'],
                gamma=0.99,
                hidden_size=2**6,
                l_rate=1e-4,
                n_inputs_n=[kwargs['env'].flatten_observation_space_n[j].shape[0]
                            for j in range(kwargs['agents'])],
                n_outputs=kwargs['env'].action_space.n,
            )
        elif cfg['game']['algorithm'] == 'ppo':
            return PPO(
                env=kwargs['env'],
                num_agents=kwargs['agents'],
                gamma=0.99,
                hidden_size=2 ** 6,
                l_rate=1e-4,
                n_inputs_n=[kwargs['env'].flatten_observation_space_n[j].shape[0]
                            for j in range(kwargs['agents'])],
                n_outputs=kwargs['env'].action_space.n,
                betas=(0.9, 0.999),
                K_epochs=4,
                eps_clip=0.2,
                update_timestep=round(kwargs['env'].cfg['duration'] * 0.04)

            )
        else:
            raise NotImplementedError(
                f"Given algorithm (`{cfg['game']['algorithm']}`) is not implemeneted yet!")

    @staticmethod
    def record_every_100_ep(episode_id):
        return (
            not episode_id
            or (
                episode_id
                and
                (episode_id + 1) % 100 == 0
            )
        )

    @staticmethod
    def create_env(config, width, height, hiding, seeker, walls, start_date, core_id):
        render_mode = 'rgb_array'
        env = gym.make(
            'hidenseek-v1',
            config=config,
            width=width,
            height=height,
            seeker=seeker,
            hiding=hiding,
            walls=walls
        )

        monitor_folder = 'monitor/' + start_date + '/core-' + str(core_id)
        env = multi_wrappers.MultiMonitor(
            env,
            monitor_folder,
            force=True,
            config=config,
            video_callable=Helpers.record_every_100_ep,
        )
        step_img_path = '/opt/app/static/images/core-' + \
            str(core_id) + '/last_frame.jpg'

        return env, step_img_path, [], render_mode, [[], []]

    @staticmethod
    def new_ep(env):
        # obs_n, reward_n, rewards_ep, done, fps_episode
        return env.reset(), [0, 0], [0, 0], [False, None], []

    @staticmethod
    def update_img_status(env, recording, path, render_mode):
        # 1% chance to get new frame update if monitoring enabled
        if recording and random.random() < .01:
            step_img = env.render(render_mode)
            step_img = img.fromarray(step_img, mode='RGB')
            step_img.save(path)
            step_img.close()

    @staticmethod
    def handle_gameover(winner, scores):
        if 'S' in winner:
            scores[0].append(1)
            scores[1].append(0)
        else:
            scores[0].append(0)
            scores[1].append(1)

    @staticmethod
    def cleanup(env, core_id):
        env.close()
        rm_path = Path('/opt/app/static/images/core-' + str(core_id))
        shutil.rmtree(rm_path)

    @staticmethod
    def update_metadata_status(fps, itera, iter_perc, time_elap, eta, img_path, rewards, wins, wins_moving):
        return {
            'fps': fps,
            'iteration': itera,
            'iteration_percentage': iter_perc,
            'time_elapsed': time_elap,
            'eta': eta,
            'image_path': img_path,
            'rewards': rewards,
            'wins': wins,
            'wins_moving': wins_moving,
        }

    @staticmethod
    def update_celery_metadata(core_id, curr, total, ep_iter, fps, itera, iter_perc, time_elap, img_path, eta, rewards, wins, wins_moving):
        return {
            'core_id': core_id,
            'current': curr,
            'total': total,
            'episode_iter': ep_iter,
            'status': Helpers.update_metadata_status(
                fps=fps,
                itera=itera,
                iter_perc=iter_perc,
                time_elap=time_elap,
                eta=eta,
                img_path=img_path,
                rewards=rewards,
                wins=wins,
                wins_moving=wins_moving,
            ),
        }

    @staticmethod
    def get_celery_success(core_id, time_elap, fps_batch, wins, ):
        return {
            'core_id': core_id,
            'time_elapsed': time_elap,
            'fps_peak': round(max(fps_batch)),
            'fps_lower': round(min(fps_batch)),
            'fps_mean': round(statistics.fmean(fps_batch)),
            'fps_median': round(statistics.median(fps_batch)),
            'fps_quantiles': [round(quantile) for quantile in statistics.quantiles(fps_batch)],
            'wins': wins,
        }
