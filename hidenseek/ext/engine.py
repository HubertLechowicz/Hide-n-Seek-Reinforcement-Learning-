import pygame
import math
import copy
from objects.controllable import Hiding, Seeker
from objects.fixed import Wall
from ext.supportive import Point, Collision, MapGenerator

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

    def init(self):
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
        map_bmp = MapGenerator.open_bmp(self.map_path)
        all_objects = MapGenerator.get_objects_coordinates(
            map_bmp, MapGenerator.get_predefined_palette())

        self.width, self.height = map_bmp.size
        logger_engine.info(f"\tResolution: {self.width}x{self.height}")

        logger_engine.info("\tWalls Sprite Group")
        self.walls_group = pygame.sprite.Group()

        logger_engine.info(f"\tGenerating map from BMP ({self.map_path})")
        for obj in all_objects:
            center_x = (obj["vertices"][0]["x"] + obj["vertices"][1]["x"]) / 2
            center_y = (obj["vertices"][0]["y"] + obj["vertices"][1]["y"]) / 2

            obj_width = obj["vertices"][1]["x"] - obj["vertices"][0]["x"]
            obj_height = obj["vertices"][1]["y"] - obj["vertices"][0]["y"]
            obj_size = (obj_width, obj_height)

            if(obj["type"] == "wall"):
                logger_engine.info("\t\tWall")
                self.walls_group.add(
                    Wall(None, center_x, center_y, obj_size))

            elif (obj["type"] == "seeker"):
                logger_engine.info("\t\tSeeker Agent")
                self.player_seek = Seeker(self.p_seek_cfg, obj_size, (center_x, center_y), (
                    255, 255, 255), self.width, self.height, (255, 255, 0))

            elif (obj["type"] == "hider"):
                logger_engine.info("\t\tHiding Agent")
                self.player_hide = Hiding(self.p_hide_cfg, obj_size, (center_x, center_y), (
                    255, 0, 0), self.width, self.height)

        self.duration = self.cfg.getint('DURATION', fallback=60)
        self.clock = pygame.time.Clock()

        logger_engine.info("Initializing Environment Objects")

        self.player_seek.update_vision({'walls': [], 'enemy': None, })
        self.player_hide.update_vision({'walls': [], 'enemy': None, })

        self.agent_env['p_seek'] = {
            'walls': Collision.get_objects_in_local_env(self.walls_group, self.player_seek.pos, self.player_seek.vision_radius, self.player_seek.direction, self.player_seek.ray_objects),
            'enemy': self.player_hide if Collision.get_objects_in_local_env([self.player_hide], self.player_seek.pos, self.player_seek.vision_radius, self.player_seek.direction, self.player_seek.ray_objects) else None,
        }
        self.agent_env['p_hide'] = {
            'walls': Collision.get_objects_in_local_env(self.walls_group, self.player_hide.pos, self.player_hide.vision_radius, self.player_hide.direction, self.player_hide.ray_objects),
            'enemy': self.player_seek if Collision.get_objects_in_local_env([self.player_seek], self.player_hide.pos, self.player_hide.vision_radius, self.player_hide.direction, self.player_hide.ray_objects) else None,
        }

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

        logger_engine.debug("\tTaking actions")
        delete_wall = self.player_seek.update(self.agent_env['p_seek'])
        if delete_wall:
            self.walls_group.remove(delete_wall)
            del delete_wall

        new_wall = self.player_hide.update(self.agent_env['p_hide'])
        if new_wall:
            self.walls_group.add(new_wall)

        self.agent_env['p_seek'] = {
            'walls': Collision.get_objects_in_local_env(self.walls_group, self.player_seek.pos, self.player_seek.vision_radius, self.player_seek.direction, self.player_seek.ray_objects),
            'enemy': self.player_hide if Collision.get_objects_in_local_env([self.player_hide], self.player_seek.pos, self.player_seek.vision_radius, self.player_seek.direction, self.player_seek.ray_objects) else None,
        }
        self.agent_env['p_hide'] = {
            'walls': Collision.get_objects_in_local_env(self.walls_group, self.player_hide.pos, self.player_hide.vision_radius, self.player_hide.direction, self.player_hide.ray_objects),
            'enemy': self.player_seek if Collision.get_objects_in_local_env([self.player_seek], self.player_hide.pos, self.player_hide.vision_radius, self.player_hide.direction, self.player_hide.ray_objects) else None,
        }
        logger_engine.debug("\tUpdating vision")
        logger_engine.info("\tDrawing frame")

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
        ray_obj = agent.ray_objects[:-1]  # without square object
        for obj in ray_obj:
            obj_len = len(obj)
            for i in range(obj_len):
                start = (obj[i].x, obj[i].y)
                end = (obj[(i + 1) % obj_len].x, obj[(i + 1) % obj_len].y)
                pygame.draw.line(screen, (255, 85, 55), start, end)

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

            self._draw_agent_vision(self.player_seek, self.screen)
            self._draw_agent_vision(self.player_hide, self.screen)
            self.players_group.draw(self.screen)

            pygame.display.update()
        elif mode == 'console':
            logger_engine.info("\t[Hiding Agent]")
            logger_engine.info(f"\t\tPosition: {self.player_hide.pos}")
            logger_engine.info(
                f"\t\tLocal environment: {self.agent_env['p_hide']}")
            logger_engine.info(
                f"\t\tTriangles in POV: {len(self.player_hide.ray_objects[:-1])}")
            logger_engine.info(
                f"\t\tWalls: {len([wall.pos for wall in self.walls_group if wall.owner == self.player_hide])}")

            logger_engine.info("\t[Seeker Agent]")
            logger_engine.info(f"\t\tPosition: {self.player_seek.pos}")
            logger_engine.info(
                f"\t\tLocal environment: {self.agent_env['p_seek']}")
            logger_engine.info(
                f"\t\tTriangles in POV: {len(self.player_seek.ray_objects[:-1])}")

            logger_engine.info("\t[Walls]")
            logger_engine.info(
                f"\t\tPositions: {[wall.pos for wall in self.walls_group]}")

        else:
            raise Exception(
                "Unexpected render mode, available: 'human', 'console', 'rgb_array'")
