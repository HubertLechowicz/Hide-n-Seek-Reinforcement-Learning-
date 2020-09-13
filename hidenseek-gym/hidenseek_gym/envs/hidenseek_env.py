import gym
from gym import error, spaces, utils
from gym.utils import seeding
from gym.envs.classic_control import rendering

import pygame
import sys
import numpy as np

from hidenseek_gym.config import config
from hidenseek_gym.controllable import Hiding, Seeker
from hidenseek_gym.supportive import Point, Collision


class HideNSeekEnv(gym.Env):
    metadata = {'render.modes': ['human', 'rgb_array']}

    def __init__(self):
        pygame.init()

        self.width = config['VIDEO'].getint('WIDTH', fallback=512)
        self.height = config['VIDEO'].getint('HEIGHT', fallback=512)
        self.fps = config['GAME'].getint('FPS', fallback=30)
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((self.width, self.height), 0, 32)
        self.dt = None
        self.duration = config['GAME'].getint('DURATION', fallback=60)

        self.wall_cfg = config['WALL']
        self.p_hide_cfg = config['AGENT_HIDING']
        self.p_seek_cfg = config['AGENT_SEEKER']

        self.player_seek = Seeker(
            self.screen, self.p_seek_cfg, (.1, .1), (255, 255, 255), self.width, self.height, (255, 255, 0))
        self.player_hide = Hiding(
            self.screen, self.p_hide_cfg, (.7, .7), (255, 0, 0), self.width, self.height, self.wall_cfg)

        self.viewer = None

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
            logger_engine.info(
                "Rectangle collision, checking Polygon Collision by using SAM Method.")
            if Collision.sat(self.player_seek.get_abs_vertices(), self.player_hide.get_abs_vertices()):
                logger_engine.info("Polygon Collision! Ending the game!")
                return True, "SEEKER"
        return False, None

    def step(self, action_n):
        obs_n = list()
        reward_n = list()
        done_n = list()
        info_n = {'n': []}

        self.screen.fill((0, 0, 0))
        self.dt = self.clock.tick_busy_loop(self.fps)

        seconds_per_frame = self.dt / 1000.
        self.player_seek.velocity = seconds_per_frame
        self.player_hide.velocity = seconds_per_frame

        ################################
        # PLAYER_HIDE then PLAYER_SEEK #
        ################################

        obs_n = [self.get_agent_vision(self.player_hide, self.player_seek), self.get_agent_vision(
            self.player_seek, self.player_hide)]
        # there should be agent action, probably w/o walls_group
        self.player_hide.update(obs_n[0], self.walls_group)
        # there should be agent action, probably w/o walls_group
        self.player_seek.update(obs_n[1], self.walls_group)

        obs_n = [self.get_agent_vision(self.player_hide, self.player_seek), self.get_agent_vision(
            self.player_seek, self.player_hide)]

        self.walls_group.draw(self.screen)
        self.player_hide.update_vision(self.screen, obs_n[0])
        self.player_seek.update_vision(self.screen, obs_n[1])

        self.players_group.draw(self.screen)
        self.duration -= seconds_per_frame

        # THER SHOULD BE CHECK FIRST FOR HIDE PLAYER IF HE DID CREATE WALL (IF YES, THEN GIVE HIM POINTS), MOVE OR ROTATE
        # THER SHOULD BE CHECK SECOND FOR SEEKER PLAYER IF HE DID CREATE WALL (IF YES, THEN GIVE HIM POINTS), MOVE OR ROTATE
        # AS FOR NOW IT'S HARD-CODED
        reward_n = [1, 1]
        done_n = [False, False]

        if self.game_over()[0]:
            done_n = [True, True]

        return obs_n, reward_n, done_n, info_n

    def reset(self):
        self.__init__()

    def get_agent_vision(self, agent, enemy):
        return {
            'walls': self.walls_in_local_env(agent.vision, agent.ray_objects, multi=True),
            'enemy': enemy if Collision.circle_with_rect(agent.vision, enemy.rect) else None,
        }

    def get_state(self):
        state = np.fliplr(np.flip(np.rot90(pygame.surfarray.array3d(
            pygame.display.get_surface()).astype(np.uint8))))
        return state

    def play(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

        # there should be Agent Action Pick
        self.step([1, 1])  # should be Discrete here
        pygame.display.update()

        gameover, winner = self.game_over()
        if gameover:
            pygame.quit()
            sys.exit()
        print(f"Winner: {winner}")

    def render(self, mode='human', close=False):
        img = self.get_state()
        if mode == 'human':
            if self.viewer is None:
                self.viewer = rendering.SimpleImageViewer()
            self.viewer.imshow(img)
        elif mode == 'rgb_array':
            return img

    def walls_in_local_env(self, circle, vertices, multi=False):
        in_radius = []
        for wall in self.walls_group:
            if multi:
                if Collision.circle_with_rect(circle, wall.rect):
                    for vertices_obj in vertices:
                        if Collision.sat(wall.get_abs_vertices(), vertices_obj):
                            in_radius.append(wall)
                            break
            else:
                if Collision.circle_with_rect(circle, wall.rect) and Collision.sat(wall.get_abs_vertices(), vertices):
                    in_radius.append(wall)
                    continue

        return in_radius
