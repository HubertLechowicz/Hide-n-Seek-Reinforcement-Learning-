import pygame
from ext.supportive import Point, Collision
from objects.fixed import Wall
import copy
import random
import json

from ext.loggers import LOGGING_DASHES, logger_seeker, logger_hiding

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

        self.speed = speed # speed ratio for player
        self.velocity = 0
        self.vision = None

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
                'type': 'NOOP', # do nothing
            },
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

    def move_action(self, new_pos):
        old_pos = copy.deepcopy(self.pos)
        self.pos = new_pos

        if old_pos != self.pos: # if moving
            self.image_index = (self.image_index + 1) % len(self.images)
            if not self.image_index: 
                self.image_index += 1

            if self.pos.y - self.height / 2 <= 0:
                self.pos.y = self.height / 2

            elif self.pos.y + self.height / 2 >= self.SCREEN_HEIGHT:
                self.pos.y = self.SCREEN_HEIGHT - self.height / 2

            if self.pos.x - self.width / 2 <= 0:
                self.pos.x = self.width / 2

            elif self.pos.x + self.width / 2 >= self.SCREEN_WIDTH:
                self.pos.x = self.SCREEN_WIDTH - self.width / 2

            self.rect.center = (self.pos.x, self.pos.y)
        else: # if not moving
            self.image_index = 0

        self.image = self.images[self.image_index]

    def take_action(self, local_env, walls_group):
        raise NotImplementedError("This is an abstract function of base class Player, please define it within class you created and make sure you don't use Player class.")

    def update(self, action):
        raise NotImplementedError("This is an abstract function of base class Player, please define it within class you created and make sure you don't use Player class.")

class Hiding(Player):
    def __init__(self, width, height, speed, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT, walls_max=5):
        super().__init__(width, height, speed, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT)

        logger_hiding.info(f"{LOGGING_DASHES} Creating New Hiding Agent (probably new game) {LOGGING_DASHES} ")
        logger_hiding.info("Initializing object")
        logger_hiding.info(f"\tSize: {self.width}x{self.height}")
        logger_hiding.info(f"\tPosition: {self.pos_init}")
        logger_hiding.info(f"\tSpeed: {self.speed}")
        logger_hiding.info(f"\tSprite: ---PLACEHOLDER---")
        logger_hiding.info(f"\tSprite for Animation: ---PLACEHOLDER---")
        
        self.walls_counter = 0
        self.walls_max = walls_max
        logger_hiding.info(f"\tWalls/Max: {self.walls_counter}/{self.walls_max}")

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

    def add_wall(self, direction, walls_group, enemy):
        logger_hiding.info("Checking if it's possible to create new wall")
        if self.walls_counter < self. walls_max:
            logger_hiding.info(f"\tAdding Wall #{self.walls_counter + 1}")
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
                raise ValueError(f"Can't create Wall. Given direction is unknown. 1 - UP, 2 - RIGHT, 3 - DOWN, 4 - LEFT")
            
            wall = Wall(self, wall_width, wall_height, wall_pos.x, wall_pos.y)
            logger_hiding.info(f"\t\tSize: {wall_width}x{wall_height}")
            logger_hiding.info(f"\t\tPosition: {wall_pos}")

            can_create = True

            for _wall in walls_group:
                if Collision.aabb(wall.pos, (wall.width, wall.height), _wall.pos, (_wall.width, _wall.height)):
                    logger_hiding.info(f"\tCouldn't add Wall #{self.walls_counter + 1}, because it would overlap with other Wall.")
                    can_create = False
                    break
            if enemy and Collision.aabb(enemy.pos, (enemy.width, enemy.height), wall.pos, (wall.width, wall.height)):
                logger_hiding.info(f"\tCouldn't add Wall #{self.walls_counter + 1}, because it would overlap with Enemy Agent")
                can_create = False
            
            if can_create:
                self.walls_counter += 1
                walls_group.add(wall)
                logger_hiding.info(f"\tAdded wall #{self.walls_counter}")
            else:
                del wall
        else:
            logger_hiding.info(f"\tLimit reached")


    def update(self, local_env, walls_group):
        new_action = copy.deepcopy(random.choice(self.actions))

        if new_action['type'] == 'NOOP':
           logger_hiding.info("NOOP! NOOP!")
        elif new_action['type'] == 'movement':
            logger_hiding.info(f"Moving to {new_action['content']}")
            new_pos = (self.pos + self.velocity * new_action['content'] * self.speed).round(4)
            logger_hiding.info(f"\tNew Position {new_pos}, checking collisions with other Objects")

            for wall in local_env['walls']:
                if Collision.aabb(new_pos, (self.width, self.height), wall.pos, (wall.width, wall.height)):
                    logger_hiding.info("\tCollision with some Wall! Not moving anywhere")
                    self.move_action(self.pos)
                    return
            self.move_action(new_pos)
        elif new_action['type'] == 'add_wall':
            self.add_wall(new_action['content'], walls_group, local_env['enemy'])

    def __str__(self):
        return "[Hiding Agent]"

class Seeker(Player):
    def __init__(self, width, height, speed, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT, color_anim):
        super().__init__(width, height, speed, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT, color_anim)

        logger_seeker.info(f"{LOGGING_DASHES} Creating New Seeker Agent (probably new game) {LOGGING_DASHES} ")
        logger_seeker.info("Initializing object")
        logger_seeker.info(f"\tSize: {self.width}x{self.height}")
        logger_seeker.info(f"\tPosition: {self.pos_init}")
        logger_seeker.info(f"\tSpeed: {self.speed}")
        logger_seeker.info(f"\tSprite: ---PLACEHOLDER---")
        logger_seeker.info(f"\tSprite for Animation: ---PLACEHOLDER---")

        self.actions += [
            {
                'type': 'remove_wall',
            },
        ]

    def remove_wall(self, wall, walls_group):
        logger_seeker.info(f"Removed wall {wall.pos}")
        walls_group.remove(wall)
        wall.owner.walls_counter -= 1
        del wall

    def update(self, local_env, walls_group):
        new_action = copy.deepcopy(random.choice(self.actions))

        if new_action['type'] == 'NOOP':
            logger_seeker.info("NOOP! NOOP!")
        elif new_action['type'] == 'movement':
            logger_seeker.info(f"Moving to {new_action['content']}")
            new_pos = (self.pos + self.velocity * new_action['content'] * self.speed).round(4)
            logger_seeker.info(f"\tNew Position {new_pos}, checking collisions with other Objects")

            for wall in local_env['walls']:
                if Collision.aabb(new_pos, (self.width, self.height), wall.pos, (wall.width, wall.height)):
                    logger_seeker.info("\tCollision with some Wall! Not moving anywhere")
                    self.move_action(self.pos)
                    return
            self.move_action(new_pos)
        elif new_action['type'] == 'remove_wall':
            if local_env['walls']:
                new_action['content'] = random.choice(local_env['walls'])
                self.remove_wall(new_action['content'], walls_group)
            else:
                logger_seeker.info(f"No Wall to remove, doing... nothing.")
        
    def __str__(self):
        return "[Seeker]"
