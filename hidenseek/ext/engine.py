import pygame

from objects.controllable import Hiding, Seeker
from objects.fixed import Wall
from ext.supportive import Point, Collision

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

    def setup(self):
        self.screen = pygame.display.set_mode((self.width, self.height), 0, 32)
        self.clock = pygame.time.Clock()

    def draw(self, should_draw):
        if should_draw:
            pygame.display.update()

    def init(self):
        self.player_seek = Seeker(50, 50, self.p_seek_speed_ratio, (.1, .1), (255, 255, 255), self.width, self.height, (255, 255, 0))
        self.player_hide = Hiding(50, 50, self.p_hide_speed_ratio, (.7, .7), (255, 0, 0), self.width, self.height, 5)

        self.player_seek.vision = pygame.draw.circle(self.screen, (0, 255, 255), (int(self.player_seek.pos.x), int(self.player_seek.pos.y)), 5 + self.player_seek.width, 1)
        self.player_hide.vision = pygame.draw.circle(self.screen, (0, 255, 255), (int(self.player_hide.pos.x), int(self.player_hide.pos.y)), 5 + self.player_hide.width, 1)

        self.players_group = pygame.sprite.Group()
        self.players_group.add(self.player_seek)
        self.players_group.add(self.player_hide)

        self.walls_group = pygame.sprite.Group()
    
    def reset(self):
        # it just uses init function
        self.init()

    def game_over(self):
        return Collision.aabb(self.player_seek.pos, (self.player_seek.width, self.player_seek.height), self.player_hide.pos, (self.player_hide.width, self.player_hide.height))

    def step(self):
        # clean screen
        self.screen.fill((0, 0, 0))
        self.dt = self.clock.tick_busy_loop(self.fps)
        self.player_seek.velocity = self.dt / 1000.
        self.player_hide.velocity = self.dt / 1000.

        player_seek_env = {
            'walls': self.walls_in_radius(self.player_seek.vision),
            'enemy': self.player_hide if Collision.circle_with_rect(self.player_seek.vision, self.player_hide.rect) else None,
        }
        player_hide_env = {
            'walls': self.walls_in_radius(self.player_hide.vision),
            'enemy': self.player_seek if Collision.circle_with_rect(self.player_hide.vision, self.player_seek.rect) else None,
        }

        self.player_seek.update(player_seek_env, self.walls_group)
        self.player_hide.update(player_hide_env, self.walls_group)

        self.player_hide.vision = pygame.draw.circle(self.screen, (0, 255, 255), (int(self.player_hide.pos.x), int(self.player_hide.pos.y)), 5 + self.player_hide.width, 1)
        self.player_seek.vision = pygame.draw.circle(self.screen, (0, 255, 255), (int(self.player_seek.pos.x), int(self.player_seek.pos.y)), 5 + self.player_seek.width, 1)

        self.players_group.draw(self.screen)
        self.walls_group.draw(self.screen)


    def walls_in_radius(self, circle):
        in_radius = []

        for wall in self.walls_group:
            if Collision.circle_with_rect(circle, wall.rect):
                in_radius.append(wall)

        return in_radius
