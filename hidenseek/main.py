import pygame
import random

from objects.Player import Player
from ext.Point import Point

class HideNSeek(object):
    def __init__(self, width, height, fps, p1_speed_ratio):
        self.width = width
        self.height = height
        self.fps = fps
        self.clock = None
        self.screen = None

        self.p1_speed_ratio = p1_speed_ratio

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
        self.player_1 = Player(50, 50, self.p1_speed_ratio * 50, (.1, .1), (255, 255, 255), self.width, self.height)
        self.player_2 = Player(50, 50, self.p1_speed_ratio * 50, (.7, .7), (255, 0, 0), self.width, self.height)

        self.players_group = pygame.sprite.Group()
        self.players_group.add(self.player_1)
        self.players_group.add(self.player_2)

    def reset(self):
        # it just uses init function
        self.init()

    def game_over(self):
        return self.player_1.rect.colliderect(self.player_2.rect)

    def step(self, dt):
        # every dt action, otherwise it freeze
        dt /= 1000.0
        self.screen.fill((0, 0, 0))

        # temporarily move them randomly
        self.player_1.update(Point((random.randint(-5, 5), random.randint(-5, 5))), dt)
        self.player_2.update(Point((random.randint(-5, 5), random.randint(-5, 5))), dt)

        self.players_group.draw(self.screen)

if __name__ == "__main__":
    fps = 60
    pygame.init()
    game = HideNSeek(width=512, height=512, fps=fps, p1_speed_ratio=.9)
    game.setup()
    game.init()

    while True:
        ##### temporarily, before agents
        if(game.game_over()):
            break
        #####
        dt = game.clock.tick_busy_loop(fps)
        game.step(dt)
        pygame.display.update()