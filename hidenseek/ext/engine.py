import pygame
import random

from objects.controllable import Hiding, Seeker
from objects.fixed import Wall
from ext.supportive import Point

class HideNSeek(object):
    def __init__(self, width, height, fps, speed_ratio, speed_multiplier):
        self.width = width
        self.height = height
        self.fps = fps
        self.clock = None
        self.screen = None

        self.p_hide_speed_ratio = speed_ratio['p_hide']
        self.p_seek_speed_ratio = speed_ratio['p_seek']

        self.speed_multiplier = speed_multiplier

    def setup(self):
        self.screen = pygame.display.set_mode((self.width, self.height), 0, 32)
        self.clock = pygame.time.Clock()

    def draw(self, should_draw):
        if should_draw:
            pygame.display.update()

    def tick(self):
        return self.clock.tick_busy_loop(self.fps)

    def game_state(self):
        # there will be game state, like Agent1 coord, Agent 2 coords, any other elements coords
        return {}

    def init(self):
        self.player_seek = Seeker(50, 50, self.p_seek_speed_ratio * self.speed_multiplier, (.1, .1), (255, 255, 255), self.width, self.height, (255, 255, 0))
        self.player_hide = Hiding(50, 50, self.p_hide_speed_ratio * self.speed_multiplier, (.7, .7), (255, 0, 0), self.width, self.height, 5)

        self.walls = []
        # self.walls = [Wall(
        #                 30 + i * 30, 
        #                 10, 
        #                 self.width * .2 + self.width * i / 10, 
        #                 self.height * .1 + self.height * i / 10)
        #     for i in range(4)
        # ]

        self.players_group = pygame.sprite.Group()
        self.players_group.add(self.player_seek)
        self.players_group.add(self.player_hide)

        self.walls_group = pygame.sprite.Group()
        # self.walls_group.add(self.walls)
    
    def reset(self):
        # it just uses init function
        self.init()

    def game_over(self):
        return self.player_seek.rect.colliderect(self.player_hide.rect)

    def step(self, dt):
        # every dt action, otherwise it freeze
        dt /= 1000.0
        self.screen.fill((0, 0, 0))

        player_seek_action = self.player_seek.take_action()
        player_hide_action = self.player_hide.take_action()

        if player_seek_action['type'] == 'remove_wall':
            walls = self.walls_in_radius(self.player_seek, radius=10)

            for wall in walls:
                player_seek_action['content'] = wall
                self.player_seek.update(player_seek_action, dt)
        else:
            self.player_seek.update(player_seek_action, dt)

        new_wall = self.player_hide.update(player_hide_action, dt)

        if new_wall:
            self.walls_group.add(new_wall)

        self.players_group.draw(self.screen)
        self.walls_group.draw(self.screen)

    def walls_in_radius(self, seeker, radius):
        in_radius = []
        radius_point = Point((radius, radius))
        seeker_radius_rect = [
            Point((min(0, seeker.pos.x - seeker.width / 2), min(0, seeker.pos.y - seeker.height / 2))) - radius_point, # top-left radius corner
            Point((max(self.width, seeker.pos.x + seeker.width / 2), min(self.height, seeker.pos.y + seeker.height / 2))) + radius_point, # top-left radius corner
        ]
        for wall in self.walls:
            if wall.pos.x + wall.width / 2 <= seeker_radius_rect[0].x or wall.pos.x - wall.width / 2 >= seeker_radius_rect[1].x:
                continue
            if wall.pos.y + wall.height / 2 <= seeker_radius_rect[0].y or wall.pos.y - wall.height / 2 >= seeker_radius_rect[1].y:
                continue

            in_radius.append(wall)

        return in_radius
