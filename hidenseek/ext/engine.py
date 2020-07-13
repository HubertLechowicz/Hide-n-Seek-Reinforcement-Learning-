import pygame

from objects.controllable import Hiding, Seeker
from objects.fixed import Wall
from ext.supportive import Point, Collision

from ext.loggers import LOGGING_DASHES, logger_engine

class HideNSeek(object):
    def __init__(self, width, height, fps, speed_ratio):
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
        logger_engine.info("Setting up Environment")
        logger_engine.info("\tCreating display")
        self.screen = pygame.display.set_mode((self.width, self.height), 0, 32)
        logger_engine.info("\tInitializing Clock")
        self.clock = pygame.time.Clock()

    def init(self):
        logger_engine.info("Initializing Environment Objects")
        logger_engine.info("\tSeeker Agent")
        self.player_seek = Seeker(50, 50, self.p_seek_speed_ratio, (.1, .1), (255, 255, 255), self.width, self.height, (255, 255, 0))
        logger_engine.info("\tSeeker Vision")
        self.player_seek.vision = pygame.draw.circle(self.screen, (0, 255, 255), (int(self.player_seek.pos.x), int(self.player_seek.pos.y)), 5 + self.player_seek.width, 1)

        logger_engine.info("\tHiding Agent")
        self.player_hide = Hiding(50, 50, self.p_hide_speed_ratio, (.7, .7), (255, 0, 0), self.width, self.height, 5)
        logger_engine.info("\tHiding Vision")
        self.player_hide.vision = pygame.draw.circle(self.screen, (0, 255, 255), (int(self.player_hide.pos.x), int(self.player_hide.pos.y)), 5 + self.player_hide.width, 1)

        logger_engine.info("\tAgents Sprite Group")
        self.players_group = pygame.sprite.Group()
        self.players_group.add(self.player_seek)
        self.players_group.add(self.player_hide)

        logger_engine.info("\tWalls Sprite Group")
        self.walls_group = pygame.sprite.Group()
    
    def reset(self):
        # it just uses init function
        logger_engine.info(f"{LOGGING_DASHES} Resetting Game {LOGGING_DASHES}")
        self.init()

    def game_over(self):
        return Collision.aabb(self.player_seek.pos, (self.player_seek.width, self.player_seek.height), self.player_hide.pos, (self.player_hide.width, self.player_hide.height))

    def step(self):
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
            'walls': self.walls_in_radius(self.player_seek.vision),
            'enemy': self.player_hide if Collision.circle_with_rect(self.player_seek.vision, self.player_hide.rect) else None,
        }
        player_hide_env = {
            'walls': self.walls_in_radius(self.player_hide.vision),
            'enemy': self.player_seek if Collision.circle_with_rect(self.player_hide.vision, self.player_seek.rect) else None,
        }

        logger_engine.debug("\tTaking actions")
        self.player_seek.update(player_seek_env, self.walls_group)
        self.player_hide.update(player_hide_env, self.walls_group)

        logger_engine.debug("\tUpdating vision")
        self.player_hide.vision = pygame.draw.circle(self.screen, (0, 255, 255), (int(self.player_hide.pos.x), int(self.player_hide.pos.y)), 5 + self.player_hide.width, 1)
        self.player_seek.vision = pygame.draw.circle(self.screen, (0, 255, 255), (int(self.player_seek.pos.x), int(self.player_seek.pos.y)), 5 + self.player_seek.width, 1)

        logger_engine.info("\tDrawing frame")
        self.walls_group.draw(self.screen)
        self.players_group.draw(self.screen)

    def walls_in_radius(self, circle):
        in_radius = []

        for wall in self.walls_group:
            if Collision.circle_with_rect(circle, wall.rect):
                in_radius.append(wall)

        return in_radius
