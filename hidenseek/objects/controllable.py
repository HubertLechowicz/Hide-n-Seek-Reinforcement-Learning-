import pygame
from ext.supportive import Point
from objects.fixed import Wall
import copy
import random

class Player(pygame.sprite.Sprite):
    # color_anim IS TEMPORARILY HERE, BECAUSE THERE ARE NO ANIMATION SPRITES, ONLY RECTANGLES WITH COLORS
    def __init__(self, width, height, speed, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT, color_anim=(64, 128, 240)):
        super().__init__()
        self.width = width
        self.height = height

        self.pos_init = Point((pos_ratio[0] * SCREEN_WIDTH, pos_ratio[1] * SCREEN_HEIGHT))
        self.pos = Point((pos_ratio[0] * SCREEN_WIDTH, pos_ratio[1] * SCREEN_HEIGHT))

        self.SCREEN_WIDTH = SCREEN_WIDTH
        self.SCREEN_HEIGHT = SCREEN_HEIGHT

        self.velocity = speed # how fast it should move

        image_inplace = pygame.Surface((width, height))
        image_inplace.fill(color)
        image_inplace.set_colorkey((0, 0, 0))

        self.image_index = 0
        image_movement = pygame.Surface((width, height))
        image_movement.fill(color_anim)
        image_movement.set_colorkey((0, 0, 0))

        self.images = [image_inplace] + [image_movement for _ in range(10)] # animations
        self.image = image_inplace
        self.rect = self.image.get_rect()
        self.rect.center = (self.pos_init.x, self.pos_init.y)

        # base class Player actions
        self.actions = [
            {
                'type': 'movement',
                'content': Point((-1, -1))
            },
            {
                'type': 'movement',
                'content': Point((-1, 0))
            },
            {
                'type': 'movement',
                'content': Point((-1, 1))
            },
            {
                'type': 'movement',
                'content': Point((0, -1))
            },
            {
                'type': 'movement',
                'content': Point((0, 0))
            },
            {
                'type': 'movement',
                'content': Point((0, 1))
            },
            {
                'type': 'movement',
                'content': Point((1, -1))
            },
            {
                'type': 'movement',
                'content': Point((1, 0))
            },
            {
                'type': 'movement',
                'content': Point((1, 1))
            },
        ]

    def move_action(self, movement, dt):
        old_pos = copy.deepcopy(self.pos)
        self.pos += self.velocity * Point((movement.x * dt, movement.y * dt))

        if self.pos.y - self.height / 2 <= 0:
            self.pos.y = self.height / 2

        elif self.pos.y + self.height / 2 >= self.SCREEN_HEIGHT:
            self.pos.y = self.SCREEN_HEIGHT - self.height / 2

        if self.pos.x - self.width / 2 <= 0:
            self.pos.x = self.width / 2

        elif self.pos.x + self.width / 2 >= self.SCREEN_WIDTH:
            self.pos.x = self.SCREEN_WIDTH - self.width / 2

        self.rect.center = (self.pos.x, self.pos.y)

        if old_pos != self.pos: # if moving
            self.image_index = (self.image_index + 1) % len(self.images)
            self.image = self.images[self.image_index]

    def take_action(self):
        raise NotImplementedError("This is an abstract function of base class Player, please define it within class you created and make sure you don't use Player class.")

    def update(self, action, dt):
        raise NotImplementedError("This is an abstract function of base class Player, please define it within class you created and make sure you don't use Player class.")

class Hiding(Player):
    def __init__(self, width, height, speed, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT, walls_max=5):
        super().__init__(width, height, speed, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT)

        self.walls_counter = 0
        self.walls_max = walls_max

        self.actions += [
            {
                'type': 'add_wall',
                'content': 1, # up
            },
            {
                'type': 'add_wall',
                'content': 2, # right
            },
            {
                'type': 'add_wall',
                'content': 3, # down
            },
            {
                'type': 'add_wall',
                'content': 4, # left
            },
        ]

    def add_wall(self, direction):
        if self.walls_counter < self. walls_max:
            self.walls_counter += 1


            wall_pos = copy.deepcopy(self.pos)
            wall_width = 15
            wall_height = 50

            DIST = 5

            if direction == 1:
                wall_width = 50
                wall_height = 15
                wall_pos.y = self.pos.y - self.height / 2 - wall_height / 2 - DIST
            elif direction == 2:
                wall_pos.x = self.pos.x + self.width / 2 + wall_width / 2 + DIST
            elif direction == 3:
                wall_width = 50
                wall_height = 15
                wall_pos.y = self.pos.y + self.height / 2 + wall_height / 2 + DIST
            elif direction == 4:
                wall_pos.x = self.pos.x - self.width / 2 - wall_width / 2 - DIST
            else:
                raise ValueError(f"Given direction is unknown. 1 - UP, 2 - RIGHT, 3 - DOWN, 4 - LEFT")
            
            print(f"Added wall #{self.walls_counter}")
            return Wall(self, wall_width, wall_height, wall_pos.x, wall_pos.y)

    def take_action(self):
        return random.choice(self.actions)

    def update(self, action, dt):
        if action['type'] == 'movement':
            self.move_action(action['content'], dt)
        elif action['type'] == 'add_wall':
            return self.add_wall(action['content'])
        else:
            raise ValueError(f"Given action type ({action['type']}) is unknown for game engine.")

class Seeker(Player):
    def __init__(self, width, height, speed, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT, color_anim):
        super().__init__(width, height, speed, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT, color_anim)

        self.actions += [
            {
                'type': 'remove_wall',
            },
        ]

    def remove_wall(self, wall):
        print(f"Removed wall {wall.pos}")
        del wall

    def take_action(self):
        return random.choice(self.actions)

    def update(self, action, dt):
        if action['type'] == 'movement':
            self.move_action(action['content'], dt)
        elif action['type'] == 'remove_wall':
            self.remove_wall(action['content'])
