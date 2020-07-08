import pygame
import random
import math

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

        # take Agent actions
        player_seek_action = self.player_seek.take_action()
        player_hide_action = self.player_hide.take_action()

        # draw Agent circles
        player_hide_circle = pygame.draw.circle(self.screen, (0, 255, 255), (int(self.player_hide.pos.x), int(self.player_hide.pos.y)), 5 + self.player_hide.width, 1) # last - border width, 0 - fill
        player_seek_circle = pygame.draw.circle(self.screen, (0, 0, 255), (int(self.player_seek.pos.x), int(self.player_seek.pos.y)), 5 + self.player_seek.width, 1) # last - border width, 0 - fill

        # update Agent Seeker based on its action
        if player_seek_action['type'] == 'remove_wall':
            walls = self.walls_in_radius(player_seek_circle)
            
            for wall in walls:
                wall.owner.walls_counter -= 1
                player_seek_action['content'] = wall
                self.player_seek.update(player_seek_action, dt)

            self.walls_group = pygame.sprite.Group([wall for wall in self.walls_group if wall not in walls])
        else:
            wall_rects = [wall.rect for wall in self.walls_group]
            if self.player_seek.rect.collidelist(wall_rects) >= -1 and player_seek_action['type'] == 'movement': # it returns -1 if there is no collision (intersection)
                player_seek_action['content'] *= -1 # move in other way
            self.player_seek.update(player_seek_action, dt)


        wall_rects = [wall.rect for wall in self.walls_group]
        new_wall = None

        # update Agent Hiding based on its action
        if self.player_hide.rect.collidelist(wall_rects) >= -1 and player_hide_action['type'] == 'movement': # it returns -1 if there is no collision (intersection)
            player_hide_action['content'] *= -1 # move in other way
        elif player_hide_action['type'] == 'add_wall':
            player_hide_action['walls'] = wall_rects
        new_wall = self.player_hide.update(player_hide_action, dt)

        # if Agent Hiding created a wall, add it to the Walls Sprite Group
        if new_wall:
            self.walls_group.add(new_wall)

        self.players_group.draw(self.screen)
        self.walls_group.draw(self.screen)

    def circle_rect_collision(self, circle, rect):
        if not isinstance(circle, pygame.Rect):
            raise TypeError(f"Circle is not a pygame.Rect object. It is {type(circle)}. Make sure to use pygame.Rect class for Circle - Rect Collision Detector")
        if not isinstance(rect, pygame.Rect):
            raise TypeError(f"Rectangle is not a pygame.Rect object. It is {type(rect)}. Make sure to use pygame.Rect class for Circle - Rect Collision Detector")
        
        x = circle.center[0]
        y = circle.y
        if circle.center[0] < rect.center[0]:
            x = rect.left
        elif circle.center[0] > rect.center[0]:
            x = rect.right

        if circle.center[1] < rect.center[1]:
            y = rect.top
        elif circle.center[1] > rect.center[1]:
            y = rect.bottom
        dist_x = circle.center[0] - x
        dist_y = circle.center[1] - y
        dist = math.sqrt(dist_x**2 + dist_y**2)

        if dist <= circle.width / 2:
            return True

        return False

    def walls_in_radius(self, circle):
        in_radius = []

        for wall in self.walls_group:
            if self.circle_rect_collision(circle, wall.rect):
                in_radius.append(wall)

        return in_radius


