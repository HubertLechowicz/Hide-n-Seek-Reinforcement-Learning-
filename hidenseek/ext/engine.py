import pygame
import math
from objects.controllable import Hiding, Seeker
from objects.fixed import Wall
from ext.supportive import Point, Collision

from ext.loggers import LOGGING_DASHES, logger_engine


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
        clock : pygame.time.Clock
            pygame Clock objects to lock FPS and use timer
        screen : pygame.display
            pygame module to control display window and screen
        dt : float
            time per frame (in miliseconds)
        duration : float
            gameplay maximum duration (in ticks), if no other game over event
        p_hide_cfg : configparser Object
            config for Hiding Agent
        p_seek_cfg : configparser Object
            config for Seeker Agent
        p_wall_cfg : configparser Object
            config for Wall Object
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
        setup():
            sets up the game environment
        init():
            initializes game environment object, don't confuse with built-in __init__ method
        reset():
            resets game environment
        game_over():
            checks whenever game should be ended or not
        step():
            called every frame, does everything to make game running
        walls_in_radius(circle):
            check if any of Wall objects (hidenseek.objects.fixed.Wall) collides with circle
    """

    def __init__(self, config):
        """
        Constructs all neccesary attributes for the HideNSeek Object

        Parameters
        ----------
            config : configparser Object
                contains config file in configparser (dict-like) Object
        """

        self.width = config['VIDEO'].getint('WIDTH', fallback=512)
        self.height = config['VIDEO'].getint('HEIGHT', fallback=512)
        self.fps = config['GAME'].getint('FPS', fallback=30)
        self.clock = None
        self.screen = None
        self.dt = None
        self.duration = config['GAME'].getint('DURATION', fallback=60)

        self.wall_cfg = config['WALL']
        self.p_hide_cfg = config['AGENT_HIDING']
        self.p_seek_cfg = config['AGENT_SEEKER']

        logger_engine.info("Initializing Game Engine")
        logger_engine.info(f"\tFPS: {self.fps}")
        logger_engine.info(f"\tResolution: {self.width}x{self.height}")

    def setup(self):
        """
        Setups game environment, which consists of creating display & initializing pygame.time.Clock object

        Parameters
        ----------
            None

        Returns
        -------
            None
        """

        logger_engine.info("Setting up Environment")
        logger_engine.info("\tCreating display")
        self.screen = pygame.display.set_mode((self.width, self.height), 0, 32)
        logger_engine.info("\tInitializing Clock")
        self.clock = pygame.time.Clock()

    def init(self):
        """
        Initializes game environment, which means creating Agents & their POV, 
        adding their to Sprite Group and creating Sprite Group for Walls

        Parameters
        ----------
            None

        Returns
        -------
            None
        """
        init_local_env = {
            'walls': [],
            'enemy': None,
        }

        logger_engine.info("Initializing Environment Objects")
        logger_engine.info("\tSeeker Agent")
        self.player_seek = Seeker(
            self.p_seek_cfg, (.1, .1), (255, 255, 255), self.width, self.height, (255, 255, 0))
        logger_engine.info("\tSeeker Vision")
        self.player_seek.update_vision(self.screen, init_local_env)

        logger_engine.info("\tHiding Agent")
        self.player_hide = Hiding(
            self.p_hide_cfg, (.7, .7), (255, 0, 0), self.width, self.height, self.wall_cfg)
        logger_engine.info("\tHiding Vision")
        self.player_hide.update_vision(self.screen, init_local_env)

        logger_engine.info("\tAgents Sprite Group")
        self.players_group = pygame.sprite.Group()
        self.players_group.add(self.player_seek)
        self.players_group.add(self.player_hide)

        logger_engine.info("\tWalls Sprite Group")
        self.walls_group = pygame.sprite.Group()

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

    def step(self):
        """
        Runs every frame, does:
            overwrites screen
            locks fps
            creates local environment for Agents
            updates Agents (depending on the Agent Action)
            updates Agents POV
            draws Walls & Agents

        Parameters
        ----------
            None

        Returns
        -------
            None
        """

        # clean screen
        logger_engine.info("New Frame")
        self.screen.fill((0, 0, 0))
        logger_engine.debug("\tLocking FPS")
        # makes sure to not exceed FPS Limit, self.clock.tick() is not that CPU-Heavy, not that accurate tho
        self.dt = self.clock.tick_busy_loop(self.fps)
        logger_engine.info(f"\tFPS: {self.clock.get_fps()}")

        logger_engine.debug("\tCalculating new Local Environments")
        player_seek_env = {
            'walls': self.walls_in_local_env(self.player_seek.vision, self.player_seek.ray_objects, multi=True),
            'enemy': self.player_hide if Collision.circle_with_rect(self.player_seek.vision, self.player_hide.rect) else None,
        }
        player_hide_env = {
            'walls': self.walls_in_local_env(self.player_hide.vision, self.player_hide.ray_objects, multi=True),
            'enemy': self.player_seek if Collision.circle_with_rect(self.player_hide.vision, self.player_seek.rect) else None,
        }

        logger_engine.debug("\tTaking actions")
        delete_wall = self.player_seek.update(player_seek_env)
        if delete_wall:
            self.walls_group.remove(delete_wall)
            del delete_wall

        new_wall = self.player_hide.update(player_hide_env)
        if new_wall:
            self.walls_group.add(new_wall)

        player_seek_env = {
            'walls': self.walls_in_local_env(self.player_seek.vision, self.player_seek.ray_objects, multi=True),
            'enemy': self.player_hide if Collision.circle_with_rect(self.player_seek.vision, self.player_hide.rect) else None,
        }
        player_hide_env = {
            'walls': self.walls_in_local_env(self.player_hide.vision, self.player_hide.ray_objects, multi=True),
            'enemy': self.player_seek if Collision.circle_with_rect(self.player_hide.vision, self.player_seek.rect) else None,
        }
        logger_engine.debug("\tUpdating vision")
        logger_engine.info("\tDrawing frame")
        self.walls_group.draw(self.screen)
        self.player_seek.update_vision(self.screen, player_seek_env)
        self.player_hide.update_vision(self.screen, player_hide_env)

        self.players_group.draw(self.screen)
        self.duration -= 1
        logger_engine.info(f"\tLeft: {self.duration} frames")

    def walls_in_local_env(self, circle, vertices, multi=False):
        """
        Checks if hidenseek.objects.fixed.Wall is in Agent Local Environment

        Parameters
        ----------
            circle : pygame.Rect
                circle in which walls should be found
            vertices : list of tuples
                list of Agent POV vertices

        Returns
        -------
            in_radius : list
                list of Wall objects (hidenseek.objects.fixed.Wall) being in circle (radius)
        """

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
