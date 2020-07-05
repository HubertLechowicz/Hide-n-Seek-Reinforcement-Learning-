import pygame
import random

from objects.controllable import Player
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

        # for agents, future reinforcement learning implementation
        self.actions = [['p1_noop', 'p1_up', 'p1_down', 'p1_left', 'p1_right'], ['p2_noop', 'p2_up', 'p2_down', 'p2_left', 'p2_right']]

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
        # there will be what to do when game inits/resets
        #                      width, height, speed ratio * width, pos_init, color,     screen_width, screen_height
        self.player_seek = Player(50, 50, self.p_hide_speed_ratio * self.speed_multiplier, (.1, .1), (255, 255, 255), self.width, self.height)
        self.player_hide = Player(50, 50, self.p_seek_speed_ratio * self.speed_multiplier, (.7, .7), (255, 0, 0), self.width, self.height)

        self.walls = [Wall(
                        30 + i * 30, 
                        10, 
                        self.width * .2 + self.width * i / 10, 
                        self.height * .1 + self.height * i / 10)
            for i in range(4)
        ]

        self.players_group = pygame.sprite.Group()
        self.players_group.add(self.player_seek)
        self.players_group.add(self.player_hide)

        self.walls_group = pygame.sprite.Group()
        self.walls_group.add(self.walls)
    
    def reset(self):
        # it just uses init function
        self.init()

    def game_over(self):
        return self.player_seek.rect.colliderect(self.player_hide.rect)

    def step(self, dt):
        # every dt action, otherwise it freeze
        dt /= 1000.0
        self.screen.fill((0, 0, 0))

        # temporarily move them randomly
        move = {
            'p1': Point((random.randint(-1, 1), random.randint(-1, 1))),
            'p2': Point((random.randint(-1, 1), random.randint(-1, 1))),
        }

        for wall in self.walls:
            if self.player_seek.rect.colliderect(wall.rect):
                move['p1'] *= -1
            if self.player_hide.rect.colliderect(wall.rect):
                move['p2'] *= -1

        self.player_seek.update(move['p1'], dt)
        self.player_hide.update(move['p2'], dt)

        self.players_group.draw(self.screen)
        self.walls_group.draw(self.screen)
