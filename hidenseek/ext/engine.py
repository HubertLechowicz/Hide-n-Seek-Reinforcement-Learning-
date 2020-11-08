import pygame
import math
import copy
from objects.controllable import Hiding, Seeker
from objects.fixed import Wall
from ext.supportive import Point, Collision, MapGenerator
import random
from ext.loggers import LOGGING_DASHES, logger_engine, logger_hiding, logger_seeker
import numpy as np
from ext.config import config


class HideNSeek(object):
    """
    Engine Class for Hide'n'Seek Game

    Attributes
    ----------
        width : int
            width of the game window
        height : int
            height of the game window
        fps : int
            amount of fps you want to lock on
        map_path : string
            path to the map, with *.bmp extension
        clock : pygame.time.Clock
            pygame Clock objects to lock FPS and use timer
        screen : pygame.display
            pygame module to control display window and screen
        dt : float
            time per frame (in miliseconds)
        duration : float
            gameplay maximum duration (in ticks), if no other game over event
        agent_env : dict
            stores agents local environments, which includes walls and enemies
        p_hide_cfg : configparser Object
            config for Hiding Agent
        p_seek_cfg : configparser Object
            config for Seeker Agent       
        player_seek : hidenseek.objects.controllable.Seeker
            instance of Seeker Agent
        player_hide : hidenseek.objects.controllable.Hiding
            instance of Hiding Agent
        players_group : pygame.sprite.Group
            group of Sprites for Agents (hidenseek.objects.controllable.Seeker, hidenseek.objects.controllable.Hiding)
        walls_group : pygame.sprite.Group
            group of sprites for Walls (hidenseek.objects.fixed.Wall)

    Methods
    -------
        init():
            initializes game environment object, don't confuse with built-in __init__ method
        reset():
            resets game environment
        game_over():
            checks whenever game should be ended or not
        step():
            called every frame, does everything to make game running
        _draw_agent_vision(agent, screen):
            draws agent POV to the given screen
        render(mode='human', close=False)
            renders game depending on given mode; close argument closes the pygame instance
    """

    def __init__(self, config):
        """
        Constructs all neccesary attributes for the HideNSeek Object

        Parameters
        ----------
            config : configparser Object
                contains config file in configparser (dict-like) Object
        """

        self.fps = config['GAME'].getint('FPS', fallback=30)
        self.map_path = config['GAME'].get(
            'MAP_PATH', fallback='fallback_map') + '.bmp'
        self.clock = None
        self.screen = None
        self.dt = None
        self.cfg = config['GAME']
        self.duration = None
        self.p_hide_cfg = config['AGENT_HIDING']
        self.p_seek_cfg = config['AGENT_SEEKER']
        self.agent_env = {}

        logger_engine.info("Initializing Game Engine")
        logger_engine.info(f"\tFPS: {self.fps}")

    def init(self, walls, seeker, hider, width, height):
        """
        Initializes game environment, which means creating Agents & their POV, 
        adding them to Sprite Group and creating Sprite Group for Walls

        Parameters
        ----------
            None

        Returns
        -------
            None
        """

        self.duration = self.cfg.getint('DURATION', fallback=60)
        self.clock = pygame.time.Clock()

        self.width, self.height = width, height
        logger_engine.info(f"\tResolution: {self.width}x{self.height}")

        logger_engine.info("\tWalls Sprite Group")
        self.walls_group = pygame.sprite.Group()

        self.walls_group.add(walls)
        self.player_seek = seeker
        self.player_hide = hider

        logger_engine.info("Initializing Environment Objects")
        self.player_seek.update_vision({'walls': [], 'enemy': None, })
        self.player_hide.update_vision({'walls': [], 'enemy': None, })

        self._calc_local_env()

        logger_engine.info("\tSeeker Vision")
        self.player_seek.update_vision(self.agent_env['p_seek'])

        logger_engine.info("\tHiding Vision")
        self.player_hide.update_vision(self.agent_env['p_hide'])

        logger_engine.info("\tAgents Sprite Group")
        self.players_group = pygame.sprite.Group()
        self.players_group.add(self.player_seek)
        self.players_group.add(self.player_hide)

    def reset(self):
        """
        Resets the environment by running init() function

        Parameters
        ----------
            None

        Returns
        -------
            None
        """

        # it just uses init function
        logger_engine.info(f"{LOGGING_DASHES} Resetting Game {LOGGING_DASHES}")
        self.init()

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
            is_over : boolean
                whether game ended
            winner : string or None
                who won the game, if the game ended
        """

        if self.duration <= 0:
            return True, "HIDING"

        if Collision.aabb(self.player_seek.pos, (self.player_seek.width, self.player_seek.height), self.player_hide.pos, (self.player_hide.width, self.player_hide.height)):
            logger_engine.info(
                "Rectangle collision, checking Polygon Collision by using SAT Method.")
            if Collision.sat(self.player_seek.get_abs_vertices(), self.player_hide.get_abs_vertices()):
                logger_engine.info("Polygon Collision! Ending the game!")
                return True, "SEEKER"
        return False, None

    def _can_create_wall(self, wall, enemy):
        """
        Checks whether can add Wall (if there is no collision between newly created wall, local walls and enemies)

        Parameters
        ----------
            wall : hidenseek.objects.fixed.Wall
                newly created Wall
            enemy : hidenseek.objects.controllable.Player (Hiding or Seeker) or None
                if enemy in local environment then Player instance, else None

        Returns
        -------
            can : bool
                if can create wall
        """

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
                    logger_hiding.info(
                        f"\tCouldn't add Wall #{self.player_hide.walls_counter + 1}, because something is on the way.")
                    return False

        for _wall in self.agent_env['p_hide']['walls']:
            if Collision.aabb(wall.pos, (wall.width, wall.height), _wall.pos, (_wall.width, _wall.height)):
                if Collision.sat(wall.get_abs_vertices(), _wall.get_abs_vertices()):
                    logger_hiding.info(
                        f"\tCouldn't add Wall #{self.player_hide.walls_counter + 1}, because it would overlap with other Wall.")
                    return False

        if enemy and Collision.aabb(enemy.pos, (enemy.width, enemy.height), wall.pos, (wall.width, wall.height)):
            if Collision.sat(self.player_hide.get_abs_vertices(), enemy.get_abs_vertices()):
                logger_hiding.info(
                    f"\tCouldn't add Wall #{self.player_hide.walls_counter + 1}, because it would overlap with Enemy Agent")
                return False
        return True

    def _add_wall(self):
        """
        Adds Wall

        Parameters
        ----------
            None

        Returns
        -------
            None
        """

        if self.player_hide.walls_counter < self.player_hide.walls_max and not self.player_hide.wall_timer:
            logger_hiding.info(
                f"\tAdding Wall #{self.player_hide.walls_counter + 1}")

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
                        wall_pos.y, wall_size, config['AGENT_HIDING'])
            logger_hiding.info(f"\t\tPosition: {wall_pos}")
            wall._rotate(self.player_hide.direction, wall_pos)
            if self._can_create_wall(wall, self.agent_env['p_hide']['enemy']):
                self.player_hide.walls_counter += 1
                logger_hiding.info(
                    f"\tAdded wall #{self.player_hide.walls_counter}")
                self.walls_group.add(wall)
                self.player_hide.wall_timer = copy.deepcopy(
                    self.player_hide.wall_timer_init)
            else:
                del wall

    def _remove_wall(self):
        """
        Removes (randomly chosen) Wall

        Parameters
        ----------
            None

        Returns
        -------
            None
        """
        if self.agent_env['p_seek']['walls'] and not self.player_seek.wall_timer:
            # remove closest in local env
            enemy_walls = [
                wall for wall in self.agent_env['p_seek']['walls'] if wall.owner]
            if enemy_walls:
                wall_dist = [self.player_seek.pos.distance(
                    wall.pos) for wall in enemy_walls]
                closest = wall_dist.index(min(wall_dist))
                delete_wall = enemy_walls[closest]
                delete_wall.owner.walls_counter -= 1
                self.walls_group.remove(delete_wall)
                del delete_wall
                self.player_seek.wall_timer = self.player_seek.wall_timer_init

    def _reduce_agent_cooldown(self, agent):
        """
        Reduces agent cooldown by 1 frame every update

        Parameters
        ----------
            agent : hidenseek.objects.controllable.Player
                Agent instance

        Returns
        -------
            None
        """

        if agent.wall_timer > 0:
            agent.wall_timer -= 1
        # for negative it's 0, for positive - higher than 0, needed if time-based cooldown (i.e. 5s) instead of frame-based (i.e. 500 frames)
        agent.wall_timer = max(agent.wall_timer, 0)

    def _calc_local_env(self):
        """
        Calculates local environments for Agents

        Parameters
        ----------
            None

        Returns
        -------
            None
        """

        self.agent_env['p_seek'] = {
            'walls': Collision.get_objects_in_local_env(self.walls_group, self.player_seek.pos, self.player_seek.vision_radius, self.player_seek.direction, self.player_seek.ray_objects),
            'enemy': self.player_hide if Collision.get_objects_in_local_env([self.player_hide], self.player_seek.pos, self.player_seek.vision_radius, self.player_seek.direction, self.player_seek.ray_objects) else None,
        }
        self.agent_env['p_hide'] = {
            'walls': Collision.get_objects_in_local_env(self.walls_group, self.player_hide.pos, self.player_hide.vision_radius, self.player_hide.direction, self.player_hide.ray_objects),
            'enemy': self.player_seek if Collision.get_objects_in_local_env([self.player_seek], self.player_hide.pos, self.player_hide.vision_radius, self.player_hide.direction, self.player_hide.ray_objects) else None,
        }

    def step(self):
        """
        Runs every frame, does:
            overwrites screen
            locks fps
            updates Agents (depending on the Agent Action) based on previously calculated Agent local environments
            creates local environment for Agents
            updates Agents POV
            updates game duration

        Parameters
        ----------
            None

        Returns
        -------
            None
        """

        # clean screen
        logger_engine.info("New Frame")
        logger_engine.debug("\tLocking FPS")
        self.dt = self.clock.tick_busy_loop(self.fps)
        logger_engine.info(f"\tFPS: {self.clock.get_fps()}")

        self._reduce_agent_cooldown(self.player_seek)
        self._reduce_agent_cooldown(self.player_hide)

        logger_engine.debug("\tTaking actions")
        new_action_seek = copy.deepcopy(
            random.choice(self.player_seek.actions))
        new_action_hide = copy.deepcopy(
            random.choice(self.player_hide.actions))

        if new_action_seek['type'] == 'remove_wall':
            self._remove_wall()
        else:
            self.player_seek.update(
                new_action_seek, self.agent_env['p_seek'], logger_seeker)

        if new_action_hide['type'] == 'add_wall':
            self._add_wall()
        else:
            self.player_hide.update(
                new_action_hide, self.agent_env['p_hide'], logger_hiding)

        logger_engine.debug("\tCalculating Local Environments")
        self._calc_local_env()

        logger_engine.debug("\tUpdating vision")
        self.player_seek.update_vision(self.agent_env['p_seek'])
        self.player_hide.update_vision(self.agent_env['p_hide'])

        self.duration -= 1
        logger_engine.info(f"\tLeft: {self.duration} frames")

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

        # Copy and then rotate the original image.
        copied_sprite = agent.sprites[agent.image_index].copy()

        copied_sprite = pygame.transform.rotozoom(
            copied_sprite, -agent.direction * 180 / math.pi, 1)
        copied_sprite_rect = copied_sprite.get_rect()
        copied_sprite_rect.center = (agent.pos.x, agent.pos.y)
        screen.blit(copied_sprite, copied_sprite_rect)

        agent.image = pygame.Surface((agent.width, agent.height))
        agent.image.set_colorkey((0, 0, 0))

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

        if mode == 'human':
            if close:
                pygame.quit()
                return
            if not self.screen:
                pygame.init()
                self.screen = pygame.display.set_mode(
                    (self.width, self.height), 0, 32)

            self.screen.fill((0, 0, 0))
            self.walls_group.draw(self.screen)

            if self.cfg.getint('DRAW_POV', fallback=1):
                self._draw_agent_vision(self.player_seek, self.screen)
                self._draw_agent_vision(self.player_hide, self.screen)
            self._draw_agent(self.player_hide, self.screen)
            self._draw_agent(self.player_seek, self.screen)

            self.players_group.draw(self.screen)

            pygame.display.update()
        elif mode == 'console':
            pass
        else:
            raise Exception(
                "Unexpected render mode, available: 'human', 'console', 'rgb_array'")
