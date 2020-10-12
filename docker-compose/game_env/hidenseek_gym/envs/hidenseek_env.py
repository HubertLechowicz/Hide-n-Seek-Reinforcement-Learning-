import gym
from gym import error, spaces, utils
from gym.utils import seeding

import pygame
import math
import copy
import sys
import os
import numpy as np

from game_env.hidenseek_gym.controllable import Hiding, Seeker
from game_env.hidenseek_gym.supportive import Point, Collision


class HideNSeekEnv(gym.Env):
    metadata = {'render.modes': ['human', 'rgb_array', 'console']}

    def __init__(self, config):
        self.default_cfg = config

        self.width = config['VIDEO'].getint('WIDTH', fallback=512)
        self.height = config['VIDEO'].getint('HEIGHT', fallback=512)
        self.fps = config['GAME'].getint('FPS', fallback=30)
        self.clock = None
        self.screen = None
        self.dt = None
        self.cfg = config['GAME']
        self.duration = None

        self.wall_cfg = config['WALL']
        self.p_hide_cfg = config['AGENT_HIDING']
        self.p_seek_cfg = config['AGENT_SEEKER']
        self.agent_env = {}

        init_local_env = {
            'walls': [],
            'enemy': None,
        }
        self.duration = self.cfg.getint('DURATION', fallback=60)
        self.clock = pygame.time.Clock()

        self.player_seek = Seeker(
            self.p_seek_cfg, (.1, .1), (255, 255, 255), self.width, self.height, (255, 255, 0))
        self.player_seek.update_vision(init_local_env)

        self.player_hide = Hiding(
            self.p_hide_cfg, (.7, .7), (255, 0, 0), self.width, self.height, self.wall_cfg)
        self.player_hide.update_vision(init_local_env)

        self.agent_env['p_seek'] = copy.deepcopy(init_local_env)
        self.agent_env['p_hide'] = copy.deepcopy(init_local_env)

        self.players_group = pygame.sprite.Group()
        self.players_group.add(self.player_seek)
        self.players_group.add(self.player_hide)

        self.walls_group = pygame.sprite.Group()

    def game_over(self):
        """
        Whenever game should end or not. Events:
        - checks whether game duration exceeded given time
        - checks the collision between 2 Agents by using 2 methods: AABB and - if first return POSSIBLE collision - SAT

        Parameters
        ----------
            None

        Returns
        -------
            None
        """

        if self.duration <= 0:
            return True, "HIDING"

        if Collision.aabb(self.player_seek.pos, (self.player_seek.width, self.player_seek.height), self.player_hide.pos, (self.player_hide.width, self.player_hide.height)):
            if Collision.sat(self.player_seek.get_abs_vertices(), self.player_hide.get_abs_vertices()):
                return True, "SEEKER"
        return False, None

    def step(self, action_n):
        obs_n = list()
        reward_n = list()
        done = False
        info_n = {'n': []}

        self.dt = self.clock.tick_busy_loop(self.fps)

        ################################
        # PLAYER_HIDE then PLAYER_SEEK #
        ################################

        # Hiding Agent Action
        new_wall = self.player_hide.update(self.agent_env['p_hide'])
        if new_wall:
            self.walls_group.add(new_wall)

        # Seeker Agent Action
        delete_wall = self.player_seek.update(self.agent_env['p_seek'])
        if delete_wall:
            self.walls_group.remove(delete_wall)
            del delete_wall

        self.agent_env['p_seek'] = {
            'walls': Collision.get_objects_in_local_env(self.walls_group, self.player_seek.pos, self.player_seek.vision_radius, self.player_seek.direction, self.player_seek.ray_objects),
            'enemy': self.player_hide if Collision.get_objects_in_local_env([self.player_hide], self.player_seek.pos, self.player_seek.vision_radius, self.player_seek.direction, self.player_seek.ray_objects) else None,
        }
        self.agent_env['p_hide'] = {
            'walls': Collision.get_objects_in_local_env(self.walls_group, self.player_hide.pos, self.player_hide.vision_radius, self.player_hide.direction, self.player_hide.ray_objects),
            'enemy': self.player_seek if Collision.get_objects_in_local_env([self.player_seek], self.player_hide.pos, self.player_hide.vision_radius, self.player_hide.direction, self.player_hide.ray_objects) else None,
        }

        obs_n = [self.agent_env['p_hide'], self.agent_env['p_seek']]

        self.player_hide.update_vision(obs_n[0])
        self.player_seek.update_vision(obs_n[1])

        self.duration -= 1

        # THER SHOULD BE CHECK FIRST FOR HIDE PLAYER IF HE DID CREATE WALL (IF YES, THEN GIVE HIM POINTS), MOVE OR ROTATE
        # THER SHOULD BE CHECK SECOND FOR SEEKER PLAYER IF HE DID CREATE WALL (IF YES, THEN GIVE HIM POINTS), MOVE OR ROTATE
        # AS FOR NOW IT'S HARD-CODED
        reward_n = [1, 1]

        if self.game_over()[0]:
            done = True

        return obs_n, reward_n, done, info_n

    def reset(self):
        self.__init__(self.default_cfg)

    def get_agent_vision(self, agent, enemy):
        return {
            'walls': self.walls_in_local_env(agent.vision, agent.ray_objects, multi=True),
            'enemy': enemy if Collision.circle_with_rect(agent.vision, enemy.rect) else None,
        }

    def get_state(self):
        state = np.fliplr(np.flip(np.rot90(pygame.surfarray.array3d(
            pygame.display.get_surface()).astype(np.uint8))))
        return state

    def _draw_agent_vision(self, agent, screen):
        """
        Function used only in HideNSeek class. Draws Agent POV on given Screen

        Parameters
        ----------
            agent : hidenseek.objects.controllable.Player
                agent instance, may be Player, Hiding or Seeker
            screen : pygame.Display
                game window

        Returns
        -------
            None
        """
        pygame.draw.arc(screen, (0, 255, 255), agent.rect.inflate(
            agent.height * 3, agent.width * 3), -agent.direction - agent.vision_rad / 2, -agent.direction + agent.vision_rad / 2, 1)

        pygame.draw.arc(screen, (0, 255, 255), agent.rect.inflate(
            agent.height * 3, agent.width * 3), -agent.direction - agent.vision_rad / 2, -agent.direction + agent.vision_rad / 2, 1)
        pygame.draw.line(screen, (0, 255, 0), (agent.pos.x, agent.pos.y),
                         (agent.vision_top.x, agent.vision_top.y), 1)
        ray_obj = agent.ray_objects[:-1]  # without square object
        for obj in ray_obj:
            obj_len = len(obj)
            for i in range(obj_len):
                start = (obj[i].x, obj[i].y)
                end = (obj[(i + 1) % obj_len].x, obj[(i + 1) % obj_len].y)
                pygame.draw.line(screen, (255, 85, 55), start, end)

    def render(self, mode='human', close=False):
        if mode == 'rgb_array':
            os.environ["SDL_VIDEODRIVER"] = "dummy"
        if mode == 'human' or mode == 'rgb_array':
            if close:
                pygame.quit()
                return
            if not self.screen:
                pygame.display.init()
                self.screen = pygame.display.set_mode(
                    (self.width, self.height), 0, 32)

            self.screen.fill((0, 0, 0))
            self.walls_group.draw(self.screen)

            self._draw_agent_vision(self.player_seek, self.screen)
            self._draw_agent_vision(self.player_hide, self.screen)
            self.players_group.draw(self.screen)

            pygame.display.update()
            img = self.get_state()
            return img
        elif mode == 'console':
            pass
        else:
            raise Exception(
                "Unexpected render mode, available: 'human', 'console', 'rgb_array'")
