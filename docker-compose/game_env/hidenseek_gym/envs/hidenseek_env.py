import gym
from gym import error, spaces, utils
from gym.utils import seeding

import pygame
import math
import copy
import random
import sys
import os
import numpy as np

from game_env.hidenseek_gym.controllable import Hiding, Seeker
from game_env.hidenseek_gym.fixed import Wall
from game_env.hidenseek_gym.supportive import Point, Collision


class HideNSeekEnv(gym.Env):
    metadata = {'render.modes': ['human', 'rgb_array', 'console']}

    def __init__(self, config, width, height, seeker, hiding, walls):
        self.default_cfg = config

        self.map_path = config['GAME'].get(
            'MAP_PATH', fallback='fallback_map') + '.bmp'
        self.fps = config['GAME'].getint('FPS', fallback=60)
        self.clock = pygame.time.Clock()
        self.screen = None

        self.dt = self.clock.tick_busy_loop(self.fps)
        self.cfg = config['GAME']
        self.duration = config['GAME'].getint('DURATION', fallback=60)

        self.width = width
        self.height = height

        self.walls_group = pygame.sprite.Group()
        self.env_walls = walls
        self.walls_group.add(walls)

        self.player_seek = seeker
        self.player_hide = hiding
        self.players_group = pygame.sprite.Group()
        self.players_group.add(self.player_seek)
        self.players_group.add(self.player_hide)

        self.p_hide_cfg = config['AGENT_HIDING']
        self.p_seek_cfg = config['AGENT_SEEKER']
        self.agent_env = {}
        self.action_space = spaces.Discrete(6)  # for both agents
        '''
        0 - NOOP 
        1 - FORWARD MOVEMENT
        2 - BACKWARD MOVEMENT
        3 - ROTATE RIGHT (clockwise)
        4 - ROTATE LEFT (counter-clockwise)
        5 - SPECIAL (ADD/DELETE WALL)
        '''
        self.observation_space_n = [
            spaces.Dict({
                'agent': spaces.Dict({
                    # position, assuming width=height
                    'position': spaces.Box(low=0, high=self.width, shape=(2, )),
                    'direction': spaces.Box(low=0, high=2*math.pi, shape=(1, )),
                }),
                'enemy':  spaces.Dict({
                    # position, assuming width=height, not inf if in local env
                    'position': spaces.Box(low=0, high=np.inf, shape=(2, )),
                    # direction, not inf if in local env
                    'direction': spaces.Box(low=0, high=np.inf, shape=(1, )),
                    # distance, not inf if in local env
                    'distance': spaces.Box(low=0, high=np.inf, shape=(1, )),
                }),
                'walls': spaces.Dict({
                    "positions": spaces.Tuple((spaces.Box(low=0, high=self.width, shape=(2, )), )),
                    "sizes": spaces.Tuple((spaces.Box(low=1, high=self.width, shape=(2, )), )),
                    "directions": spaces.Tuple((spaces.Box(low=0, high=2*math.pi, shape=(1, )), )),
                    "distances": spaces.Tuple((spaces.Box(low=0, high=self.width, shape=(1, )), )),
                    "owners": spaces.Tuple((spaces.Discrete(2), )),
                }),
            }),
            spaces.Dict({
                'agent': spaces.Dict({
                    # position, assuming width=height
                    'position': spaces.Box(low=0, high=self.width, shape=(2, )),
                    'direction': spaces.Box(low=0, high=2*math.pi, shape=(1, )),
                }),
                'enemy':  spaces.Dict({
                    # position, assuming width=height, not inf if in local env
                    'position': spaces.Box(low=0, high=np.inf, shape=(2, )),
                    # direction, not inf if in local env
                    'direction': spaces.Box(low=0, high=np.inf, shape=(1, )),
                    # distance, not inf if in local env
                    'distance': spaces.Box(low=0, high=np.inf, shape=(1, )),
                }),
                'walls': spaces.Dict({
                    "positions": spaces.Tuple((spaces.Box(low=0, high=self.width, shape=(2, )), )),
                    "sizes": spaces.Tuple((spaces.Box(low=1, high=self.width, shape=(2, )), )),
                    "directions": spaces.Tuple((spaces.Box(low=0, high=2*math.pi, shape=(1, )), )),
                    "distances": spaces.Tuple((spaces.Box(low=0, high=self.width, shape=(1, )), )),
                    "owners": spaces.Tuple((spaces.Discrete(2), )),
                }),
                'walls_max': spaces.Discrete(config['AGENT_HIDING'].getint('WALLS_MAX', fallback=5) + 1)
            }),
        ]

    def reset(self):
        self.duration = self.cfg.getint('DURATION', fallback=60)
        self.screen = None
        self.agent_env = {}

        self.walls_group = pygame.sprite.Group()
        self.walls_group.add(self.env_walls)

        self.player_seek.reset()
        self.player_hide.reset()

        self.player_seek.update_vision({'walls': [], 'enemy': None, })
        self.player_hide.update_vision({'walls': [], 'enemy': None, })

        self._calc_local_env()

        self.player_seek.update_vision(self.agent_env['p_seek'])
        self.player_hide.update_vision(self.agent_env['p_hide'])

        self.players_group = pygame.sprite.Group()
        self.players_group.add(self.player_seek)
        self.players_group.add(self.player_hide)

        return [
            self._get_agent_obs(self.player_seek, self.agent_env['p_seek']),
            self._get_agent_obs(self.player_hide, self.agent_env['p_hide'])
        ]

    def game_over(self):
        if self.duration <= 0:
            return True, "HIDING"

        if Collision.aabb(self.player_seek.pos, (self.player_seek.width, self.player_seek.height), self.player_hide.pos, (self.player_hide.width, self.player_hide.height)):
            if Collision.sat(self.player_seek.get_abs_vertices(), self.player_hide.get_abs_vertices()):
                return True, "SEEKER"
        return False, None

    def _can_create_wall(self, wall, enemy):
        # check if dynamically created POV lines are shorter than eyesight -- if yes, then it's not possible to create a Wall
        local_wall_edges = self.player_hide.reduce_wall_edges(
            self.agent_env['p_hide']['walls'])
        wall_vertices = wall.get_abs_vertices()
        wall_edges = [wall_vertices[0], wall.pos,
                      wall_vertices[3]]  # only closer edges & center

        vision_ray_points = [[self.player_hide.pos, wall_edge]
                             for wall_edge in wall_edges] + [[self.player_hide.pos, self.player_hide.vision_top]]
        for ray in vision_ray_points:
            ray_dist = ray[0].distance(ray[1])
            for local_wall_edge in local_wall_edges:
                p = Collision.line_intersection(ray, local_wall_edge)
                if p and p.distance(ray[0]) < ray_dist:
                    return False

        for _wall in self.agent_env['p_hide']['walls']:
            if Collision.aabb(wall.pos, (wall.width, wall.height), _wall.pos, (_wall.width, _wall.height)):
                if Collision.sat(wall.get_abs_vertices(), _wall.get_abs_vertices()):
                    return False

        if enemy and Collision.aabb(enemy.pos, (enemy.width, enemy.height), wall.pos, (wall.width, wall.height)):
            if Collision.sat(self.player_hide.get_abs_vertices(), enemy.get_abs_vertices()):
                return False
        return True

    def _add_wall(self):
        if self.player_hide.walls_counter < self.player_hide.walls_max and not self.player_hide.wall_timer:
            wall_pos = copy.deepcopy(self.player_hide.pos)
            wall_size = (max(int(self.player_hide.width / 10), 2),
                         max(int(self.player_hide.height / 2), 2))  # minimum 2x2 Wall
            vision_arc_range = np.sqrt((self.player_hide.vision_top.x - self.player_hide.pos.x) * (self.player_hide.vision_top.x - self.player_hide.pos.x) + (
                self.player_hide.vision_top.y - self.player_hide.pos.y) * (self.player_hide.vision_top.y - self.player_hide.pos.y))
            # vision arc range - 1.5 wall width, so the wall is always created inside PoV.
            wall_pos.x = wall_pos.x + vision_arc_range - \
                (1.5 * wall_size[0])
            wall_pos = Point.triangle_unit_circle_relative(
                self.player_hide.direction, self.player_hide.pos, wall_pos)

            wall = Wall(self.player_hide, wall_pos.x,
                        wall_pos.y, wall_size)
            wall._rotate(self.player_hide.direction, wall_pos)
            if self._can_create_wall(wall, self.agent_env['p_hide']['enemy']):
                self.player_hide.walls_counter += 1
                self.walls_group.add(wall)
                self.player_hide.wall_timer = copy.deepcopy(
                    self.player_hide.wall_timer_init)
            else:
                del wall

    def _remove_wall(self):
        # TODO: Implement decision-making algorithm which Wall to delete
        if self.agent_env['p_seek']['walls'] and not self.player_seek.wall_timer:
            # remove randomly selected wall in local env
            delete_wall = random.choice(self.agent_env['p_seek']['walls'])
            self.player_seek.wall_timer = self.player_seek.wall_timer_init
            if delete_wall.owner:
                delete_wall.owner.walls_counter -= 1
                self.walls_group.remove(delete_wall)
                del delete_wall

    def _reduce_agent_cooldown(self, agent):
        if agent.wall_timer > 0:
            agent.wall_timer -= 1
        # for negative it's 0, for positive - higher than 0, needed if time-based cooldown (i.e. 5s) instead of frame-based (i.e. 500 frames)
        agent.wall_timer = max(agent.wall_timer, 0)

    def _calc_local_env(self):
        self.agent_env['p_seek'] = {
            'walls': Collision.get_objects_in_local_env(self.walls_group, self.player_seek.pos, self.player_seek.vision_radius, self.player_seek.direction, self.player_seek.ray_objects),
            'enemy': self.player_hide if Collision.get_objects_in_local_env([self.player_hide], self.player_seek.pos, self.player_seek.vision_radius, self.player_seek.direction, self.player_seek.ray_objects) else None,
        }
        self.agent_env['p_hide'] = {
            'walls': Collision.get_objects_in_local_env(self.walls_group, self.player_hide.pos, self.player_hide.vision_radius, self.player_hide.direction, self.player_hide.ray_objects),
            'enemy': self.player_seek if Collision.get_objects_in_local_env([self.player_seek], self.player_hide.pos, self.player_hide.vision_radius, self.player_hide.direction, self.player_hide.ray_objects) else None,
        }

    def _get_agent_obs(self, agent, local_env):
        walls_data = [{
            'position': np.array([wall.pos.x, wall.pos.y]),
            'size': np.array([wall.width, wall.height]),
            'direction': np.array(wall.direction),
            'distance': np.array(wall.pos.distance(agent.pos)),
            'owner': 1 if wall.owner else 0,
        } for wall in local_env['walls']]

        next_obs = {
            'agent': {
                'position': np.array([agent.pos.x, agent.pos.y]),
                'direction': np.array(agent.direction),
            },
            'enemy': {
                'position': np.array([local_env['enemy'].pos.x, local_env['enemy'].pos.y] if local_env['enemy'] else [np.inf, np.inf]),
                'direction': np.array(local_env['enemy'].direction if local_env['enemy'] else np.inf),
                'distance': np.array(local_env['enemy'].pos.distance(agent.pos) if local_env['enemy'] else np.inf)
            },
            'walls': {
                'positions': tuple(wall_data['position'] for wall_data in walls_data),
                'sizes': tuple(wall_data['size'] for wall_data in walls_data),
                'directions': tuple(wall_data['direction'] for wall_data in walls_data),
                'distances': tuple(wall_data['distance'] for wall_data in walls_data),
                'owners': tuple(wall_data['owner'] for wall_data in walls_data),
            },
        }

        if isinstance(agent, Hiding):
            next_obs['walls_max'] = agent.walls_max - agent.walls_counter

        return next_obs

        '''
        0 - NOOP 
        1 -  BACKWARD MOVEMENT
        2 - FORWARD MOVEMENT
        3 - ROTATE LEFT (counter-clockwise)
        4 - ROTATE RIGHT (clockwise)
        5 - SPECIAL (ADD/DELETE WALL)
        '''

    def _rotate_agent(self, agent, turn, local_env):
        """
        Rotates the object, accordingly to the value, along its axis.

        Parameters
        ----------
            agent : object
            turn : int, [-1,1]
                in which direction should agent rotate (clockwise or counterclockwise)
            local_env : dict
                contains Player Local Environment

        Returns
        -------
            None
        """
        old_direction = copy.deepcopy(agent.direction)
        agent.direction += agent.speed_rotate * turn
        # base 2PI, because it's circle
        agent.direction = agent.direction % (2 * math.pi)

        angle = (agent.direction - old_direction)

        # Update the polygon points for collisions
        old_polygon_points = copy.deepcopy(agent.polygon_points)
        agent.polygon_points = [Point.triangle_unit_circle_relative(
            angle, Point((agent.width / 2, agent.height / 2)), polygon_point) for polygon_point in agent.polygon_points]

        for wall in local_env['walls']:
            if Collision.aabb(agent.pos, (agent.width, agent.height), wall.pos, (wall.width, wall.height)):
                if Collision.sat(agent.get_abs_vertices(), wall.get_abs_vertices()):
                    agent.polygon_points = old_polygon_points
                    agent.direction = old_direction
                    break

    def _perform_agent_action(self, agent, action, local_env):
        if action == 0:
            '''
            agent.image_index = 0
            agent.image = agent.images[agent.image_index]
            '''
            return 0
        elif action in [1, 2]:
            # (1 - 1.5) * 2 = -1, so for Forward it needs to be * (-1)
            x = math.cos(agent.direction) * agent.speed * \
                (action - 1.5) * 2 * (-1)
            # (1 - 1.5) * 2 = -1, so for Forward it needs to be * (-1)
            y = math.sin(agent.direction) * agent.speed * \
                (action - 1.5) * 2 * (-1)
            old_pos = copy.deepcopy(agent.pos)
            new_pos = agent.pos + Point((x, y))

            self._move_agent(agent, new_pos)
            for wall in local_env['walls']:
                if Collision.aabb(new_pos, (agent.width, agent.height), wall.pos, (wall.width, wall.height)):
                    if Collision.sat(agent.get_abs_vertices(), wall.get_abs_vertices()):
                        self._move_agent(agent, old_pos)
                        return
        elif action in [3, 4]:
            # (3 - 3.5) * 2 = -1, so for Clockwise Rotate it needs to be * (-1)
            self._rotate_agent(agent, (action - 3.5) * 2 * (-1), local_env)
        elif action == 5:
            if isinstance(agent, Seeker):
                self._remove_wall()
            else:
                self._add_wall()

        reward = 0
        return reward

    def _move_agent(self, agent, new_pos):
        """
        Algorithm which moves the Player object to given direction, if not outside map (game screen)

        Parameters
        ----------
            new_pos : hidenseek.ext.supportive.Point
                Point object of the new position

        Returns
        -------
            None
        """

        old_pos = copy.deepcopy(agent.pos)
        agent.pos = new_pos

        if old_pos != agent.pos:  # if moving
            agent.image_index = (agent.image_index + 1) % len(agent.images)
            if not agent.image_index:
                agent.image_index += 1
            agent.rect.center = (agent.pos.x, agent.pos.y)
        else:  # if not moving
            agent.image_index = 0

        agent.image = agent.images[agent.image_index]

    def step(self, action_n):
        obs_n = list()
        reward_n = list()
        info_n = {'n': []}

        self.dt = self.clock.tick_busy_loop(self.fps)

        self._reduce_agent_cooldown(self.player_seek)
        self._reduce_agent_cooldown(self.player_hide)

        self._perform_agent_action(
            self.player_seek, action_n[0], self.agent_env['p_seek'])
        self._perform_agent_action(
            self.player_hide, action_n[1], self.agent_env['p_hide'])

        self._calc_local_env()

        self.player_seek.update_vision(self.agent_env['p_seek'])
        self.player_hide.update_vision(self.agent_env['p_hide'])

        # REWARD SHOULD HAVE AN APPEND AT PERFORM_AGENT_ACTION
        reward_n = [random.random(), random.random()]

        done = self.game_over()

        obs_n = [
            self._get_agent_obs(self.player_seek, self.agent_env['p_seek']),
            self._get_agent_obs(self.player_hide, self.agent_env['p_hide'])
        ]

        self.duration -= 1

        return obs_n, reward_n, done, info_n

    def get_state(self):
        state = np.fliplr(np.flip(np.rot90(pygame.surfarray.array3d(
            pygame.display.get_surface()).astype(np.uint8))))
        return state

    def _draw_agent_vision(self, agent, screen):
        pygame.draw.line(screen, (0, 255, 0), (agent.pos.x, agent.pos.y),
                         (agent.vision_top.x, agent.vision_top.y), 1)
        ray_obj = agent.ray_points  # without square object
        for obj in ray_obj:
            pygame.draw.line(screen,
                             (255, 85, 55),
                             (agent.pos.x, agent.pos.y),
                             (obj.x, obj.y)
                             )

    def _draw_agent(self, agent, screen):
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
        polygon_points_tuples = [(p.x, p.y) for p in agent.polygon_points]
        image_inplace = pygame.Surface((agent.width, agent.height))
        image_inplace.set_colorkey((0, 0, 0))
        pygame.draw.polygon(image_inplace, agent.color, polygon_points_tuples)

        image_movement = pygame.Surface((agent.width, agent.height))
        image_movement.set_colorkey((0, 0, 0))

        pygame.draw.polygon(image_movement, agent.color_anim,
                            polygon_points_tuples)
        agent.images = [image_inplace] + \
            [image_movement for _ in range(10)]  # animations
        agent.image = image_inplace

    def render(self, mode='human', close=False):
        """
        Renders game based on the mode. Raises Exception if unexpected render mode.

        Parameters
        ----------
            mode : string
                mode in which game should be rendered (graphic, console, rgb_array)            
            close : boolean
                whether pygame instance should be shutdown

        Returns
        -------
            None
        """
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
            if self.walls_group:
                self.walls_group.draw(self.screen)

            if self.player_hide and self.player_seek:
                if self.cfg.getint('DRAW_POV', fallback=1):
                    self._draw_agent_vision(self.player_seek, self.screen)
                    self._draw_agent_vision(self.player_hide, self.screen)
                self._draw_agent(self.player_hide, self.screen)
                self._draw_agent(self.player_seek, self.screen)

            if self.players_group:
                self.players_group.draw(self.screen)

            pygame.display.update()
            img = self.get_state()
            return img
        elif mode == 'console':
            pass
        else:
            raise Exception(
                "Unexpected render mode, available: 'human', 'console', 'rgb_array'")
