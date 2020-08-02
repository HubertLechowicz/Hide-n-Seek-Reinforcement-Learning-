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
        p_hide_speed_ratio : float
            movement speed ratio for Hiding Agent
        p_seek_speed_ratio : float
            movement speed ratio for Seeker Agent
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

    def __init__(self, width, height, fps, speed_ratio):
        """
        Constructs all neccesary attributes for the HideNSeek Object

        Parameters
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
            p_hide_speed_ratio : float
                movement speed ratio for Hiding Agent
            p_seek_speed_ratio : float
                movement speed ratio for Seeker Agent
        """

        self.width = width
        self.height = height
        self.fps = fps
        self.clock = None
        self.screen = None
        self.dt = None
        
        self.p_hide_speed_ratio = speed_ratio['p_hide']
        self.p_seek_speed_ratio = speed_ratio['p_seek']

        logger_engine.info("Initializing Game Engine")
        logger_engine.info(f"\tFPS: {fps}")
        logger_engine.info(f"\tSpeed Ratio for Hiding Agent: {speed_ratio['p_hide']}")
        logger_engine.info(f"\tSpeed Ratio for Seeker Agent: {speed_ratio['p_seek']}")
        logger_engine.info(f"\tResolution: {width}x{height}")

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
        logger_engine.info("Initializing Environment Objects")
        logger_engine.info("\tSeeker Agent")
        self.player_seek = Seeker(50, 50, self.p_seek_speed_ratio, (.1, .1), (255, 255, 255), self.width, self.height, (255, 255, 0))
        logger_engine.info("\tSeeker Vision")
        self.player_seek.update_vision(self.screen)
        
        logger_engine.info("\tHiding Agent")
        self.player_hide = Hiding(50, 50, self.p_hide_speed_ratio, (.7, .7), (255, 0, 0), self.width, self.height, 5)
        logger_engine.info("\tHiding Vision")
        self.player_hide.update_vision(self.screen)

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
        Checks whenever game should end or not. Right now it checks the collision between 2 Agents
        by using 2 methods: AABB and - if first return POSSIBLE collision - SAT

        Parameters
        ----------
            None

        Returns
        -------
            None
        """

        if Collision.aabb(self.player_seek.pos, (self.player_seek.width, self.player_seek.height), self.player_hide.pos, (self.player_hide.width, self.player_hide.height)):
            logger_engine.info("Rectangle collision, checking Polygon Collision by using SAM Method.")
            if Collision.sat(self.player_seek.get_abs_vertices(), self.player_hide.get_abs_vertices()):
                logger_engine.info("Polygon Collision! Ending the game!")
                return True
        return False

    def step(self):
        """
        Runs every frame, does:
            overwrites screen
            locks fps
            calculates Agents 'velocity'
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
        self.dt = self.clock.tick_busy_loop(self.fps)
        logger_engine.info(f"\tFPS: {self.clock.get_fps()}")
        self.player_seek.velocity = self.dt / 1000.
        self.player_hide.velocity = self.dt / 1000.
        logger_engine.debug("\tNew Velocity for Agents")
        logger_engine.debug(f"\t\tSeeker Agent: {self.player_seek.velocity}")
        logger_engine.debug(f"\t\tHiding Agent: {self.player_hide.velocity}")

        logger_engine.debug("\tCalculating new Local Environments")
        player_seek_env = {
            'walls': self.walls_in_local_env(self.player_seek.vision, list(self.player_hide.vision_points.values())),
            'enemy': self.player_hide if Collision.circle_with_rect(self.player_seek.vision, self.player_hide.rect) else None,
        }
        player_hide_env = {
            'walls': self.walls_in_local_env(self.player_hide.vision, list(self.player_hide.vision_points.values())),
            'enemy': self.player_seek if Collision.circle_with_rect(self.player_hide.vision, self.player_seek.rect) else None,
        }

        logger_engine.debug("\tTaking actions")
        self.player_seek.update(player_seek_env, self.walls_group)
        self.player_hide.update(player_hide_env, self.walls_group)

        logger_engine.debug("\tUpdating vision")
        self.player_hide.update_vision(self.screen )
        self.player_seek.update_vision(self.screen)




        logger_engine.info("\tDrawing frame")
        self.walls_group.draw(self.screen)

        self.players_group.draw(self.screen)



    def walls_in_local_env(self, circle, vertices):
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
            if Collision.circle_with_rect(circle, wall.rect) and Collision.sat(wall.get_abs_vertices(), vertices):
                in_radius.append(wall)
        
        return in_radius
