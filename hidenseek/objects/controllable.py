import pygame
from ext.supportive import Point, Collision
from objects.fixed import Wall
import copy
import random
import json
import math
from ext.loggers import LOGGING_DASHES, logger_seeker, logger_hiding


class Player(pygame.sprite.Sprite):
    """
    Parent Player Class for Hide'n'Seek Game, inherits from pygame.sprite.Sprite.
    Shouldn't be used because it doesn't have implementation of few methods

    Attributes
    ----------
        width : int
            width of the Player Rectangle
        height : int
            height of the Player Rectangle
        SCREEN_WIDTH : int
            width of the game window
        SCREEN_HEIGHT : int
            height of the game window
        pos : hidenseek.ext.supportive.Point
            object position on the game display
        speed : float
            speed ratio for Player movement
        velocity : float
            velocity ratio for Player movement, calculated by using Game Engine FPS Lock value
        vision : pygame.Rect
            Player POV
            TODO: Probably will be standalone Object after implementing proper POV
        image_index : int
            determines which image should be drawn
        images : list of pygame.Surface
            objects with sprite/images from which the proper one will be drawn
        image : pygame.Surface
            object with sprite/image, chosen by 'image_index'
        rect : pygame.Rect
            object Rectangle, to be drawn
        polygon_points : list of tuples
            vertices, used for collision check in SAT
        actions : list of dict
            contains all possible Player actions

    Methods
    -------
        get_abs_vertices():
            returns absolute vertices coordinates (in game screen coordinates system)
        move_action(new_pos):
            algorithm which moves the Player object to given poisition
        take_action(local_env, walls_group):
            Not implemented in Parent Class
        update(local_env, walls_group):
            Not implemented in Parent Class
    """

    # color_anim IS TEMPORARILY HERE, BECAUSE THERE ARE NO ANIMATION SPRITES, ONLY RECTANGLES WITH COLORS


    def __init__(self, width, height, speed, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT, color_anim=(64, 128, 240)):
        """
        Constructs all neccesary attributes for the Player Object

        Parameters
        ----------
            width : int
                width of the Player Rectangle
            height : int
                height of the Player Rectangle
            speed : float
                speed ratio for Player movement
            pos_ratio : tuple
                used to calculate initial position of the Player in absolute coordinate system (game screen)
            color : tuple
                if no image, represents the shape fill color in RGB format, i.e. (0, 0, 0)
                TODO: ONCE USING IMAGE - DELETE THIS
            SCREEN_WIDTH : int
                width of the game window
            SCREEN_HEIGHT : int
                height of the game window
            color_anim : tuple
                if no image, represents the shape fill color for animation in RGB format, i.e. (0, 0, 0)
                TODO: ONCE USING IMAGE - DELETE THIS
        """

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
        self.vision_points = {
            'left': None,
            'top': None,
            'right': None,
            'center': None,
        }
        self.vision_rad = math.pi/6
        self.image_index = 0
        self.direction = 0  # radians from which vision_rad is added/substracted

        ############### SQUARE SPRITE ###############
        # image_inplace = pygame.Surface((width, height))
        # image_inplace.fill(color)
        # image_inplace.set_colorkey((0, 0, 0))

        # image_movement = pygame.Surface((width, height))
        # image_movement.fill(color_anim)
        # image_movement.set_colorkey((0, 0, 0))
        ############### SQUARE SPRITE ###############

        ############### POLYGON SPRITE ##############
        self.polygon_points = [(width / 2, 0), (width, .27 * height), (width, .73 * height), (width / 2, height), (0, .73 * height), (0, .27 * height)]
        image_inplace = pygame.Surface((width, height))
        image_inplace.set_colorkey((0, 0, 0))
        pygame.draw.polygon(image_inplace, color, self.polygon_points)
        pygame.draw.rect(image_inplace, (255, 255, 255), pygame.Rect(0, 0, width, height), 1)

        image_movement = pygame.Surface((width, height))
        image_movement.set_colorkey((0, 0, 0))
        pygame.draw.polygon(image_movement, color_anim, self.polygon_points)
        pygame.draw.rect(image_movement, (255, 255, 255), pygame.Rect(0, 0, width, height), 1)
        ############### POLYGON SPRITE ##############

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
                'type': 'movement'
            },
            {
                'type': 'rotation',
                'content': -1
            },
            {
                'type': 'rotation',
                'content': 1
            },

        ]

    def rotate(self,turn):
        """
        Rotates the object, accrodingly to the value, along it's axis.

        Parameters
        ----------
            turn : int, [-1,1]
                TODO XD

        Returns
        -------
            None
        """
        self.direction += self.velocity * turn

    def get_abs_vertices(self):
        """
        Returns absolute coordinates of Vertices in Polygon

        Parameters
        ----------
            None
        
        Returns
        -------
            points : list of hidenseek.ext.supportive.Point
                self.pylogon_points mapped to the absolute coordinates system
        """
        
        return [Point((x + self.rect.left, y + self.rect.top)) for x, y in self.polygon_points]

    def move_action(self, new_pos):
        """
        Algorithm which moves the Player object to given direction, if not outside map (game screen)

        Parameters
        ----------
            new_pos : hidenseek.ext.supportive.Point
                Point object of the new position

        Returns
        -------
            None
        """            
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
        """
        Not implemented in Parent Class
        """
        raise NotImplementedError("This is an abstract function of base class Player, please define it within class you created and make sure you don't use Player class.")

    def update_vision(self, display):
        """
        Updates Agent Vision

        Parameters
        ----------
            display : pygame.display
                Game Display (Window)
            triangle_unit_circle : hidenseek.ext.engine.triangle_unit_circle(radians, **kwargs)
                Function used to calculate movement/relocation in Triangle Unit Circle based on given Radians
        
        Returns
        -------
            None
        """

        self.vision = pygame.draw.arc(display, (0, 255, 255), self.rect.inflate(self.height, self.width), -self.direction - self.vision_rad / 2, -self.direction + self.vision_rad / 2, 1)

        new_point = Point.triangle_unit_circle(self.direction, side_size=self.width)
        self.vision_points['top'] = self.pos + new_point

        new_point = Point.triangle_unit_circle(self.direction - self.vision_rad / 2, side_size=self.width)
        self.vision_points['left'] = self.pos + new_point

        new_point = Point.triangle_unit_circle(self.direction + self.vision_rad / 2, side_size=self.width)
        self.vision_points['right'] = self.pos + new_point

        self.vision_points['center'] = self.pos

        pygame.draw.line(display, (255, 0, 0), (self.pos.x, self.pos.y), (self.vision_points['top'].x, self.vision_points['top'].y))
        pygame.draw.line(display, (0, 255, 255), (self.pos.x, self.pos.y), (self.vision_points['left'].x, self.vision_points['left'].y))
        pygame.draw.line(display, (0, 255, 255), (self.pos.x, self.pos.y), (self.vision_points['right'].x, self.vision_points['right'].y))

    def update(self, local_env, walls_group):
        """
        Not implemented in Parent Class
        """
        raise NotImplementedError("This is an abstract function of base class Player, please define it within class you created and make sure you don't use Player class.")


class Hiding(Player):
    """
    Child Hiding Class for Hide'n'Seek Game, inherits from Player.

    Attributes
    ----------
        width : int
            width of the Player Rectangle
        height : int
            height of the Player Rectangle
        SCREEN_WIDTH : int
            width of the game window
        SCREEN_HEIGHT : int
            height of the game window
        pos : hidenseek.ext.supportive.Point
            object position on the game display
        speed : float
            speed ratio for Player movement
        velocity : float
            velocity ratio for Player movement, calculated by using Game Engine FPS Lock value
        vision : pygame.Rect
            Player POV
            TODO: Probably will be standalone Object after implementing proper POV
        image_index : int
            determines which image should be drawn
        images : list of pygame.Surface
            objects with sprite/images from which the proper one will be drawn
        image : pygame.Surface
            object with sprite/image, chosen by 'image_index'
        rect : pygame.Rect
            object Rectangle, to be drawn
        polygon_points : list of tuples
            vertices, used for collision check in SAT
        actions : list of dict
            contains all possible Player actions
        walls_counter : int
            existing hidenseek.objects.fixes.Wall objects made by Hiding Player
        walls_max : int
            maximum amount of existing hidenseek.objects.fixes.Wall objects that may be created by Hiding Player 

    Methods
    -------
        get_abs_vertices():
            returns absolute vertices coordinates (in game screen coordinates system)
        move_action(new_pos):
            algorithm which moves the Player object to given poisition
        add_wall(direction, walls_group, enemy):
            creates new hidenseek.objects.fixes.Wall object and adds it to the game if no collision
        update(local_env, walls_group):
            takes and performs the action
    """

    def __init__(self, width, height, speed, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT, walls_max=5):
        """
        Constructs all neccesary attributes for the Hiding Object

        Parameters
        ----------
            width : int
                width of the Player Rectangle
            height : int
                height of the Player Rectangle
            speed : float
                speed ratio for Player movement
            pos_ratio : tuple
                used to calculate initial position of the Player in absolute coordinate system (game screen)
            color : tuple
                if no image, represents the shape fill color in RGB format, i.e. (0, 0, 0)
                TODO: ONCE USING IMAGE - DELETE THIS
            SCREEN_WIDTH : int
                width of the game window
            SCREEN_HEIGHT : int
                height of the game window
            walls_max : int
                maximum amount of existing hidenseek.objects.fixes.Wall objects that may be created by Hiding Player 
        """

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
            }
        ]



    def add_wall(self, walls_group, enemy):
        """
        Creates new hidenseek.objects.fixes.Wall object and adds it to the game if no collision

        Parameters
        ----------
            walls_group : list of hidenseek.objects.fixes.Wall
                contains all walls in the area
                TODO: Once Agent POV done - REPLACE WITH local_env['walls']
            enemy : hidenseek.objects.controllable.Seeker, None
                if enemy in radius then it contains its object, else None
        
        Returns
        -------
            None
        """

        logger_hiding.info("Checking if it's possible to create new wall")
        if self.walls_counter < self. walls_max:
            logger_hiding.info(f"\tAdding Wall #{self.walls_counter + 1}")
            wall_pos = copy.deepcopy(self.vision_points['top'])
            wall_width = 25
            wall_height = 50


            wall = Wall(self, wall_width, wall_height, wall_pos.x, wall_pos.y)
            logger_hiding.info(f"\t\tSize: {wall_width}x{wall_height}")
            logger_hiding.info(f"\t\tPosition: {wall_pos}")
            wall.rotate(self.direction,wall_pos)

            can_create = True

            for _wall in walls_group:
                if Collision.aabb(wall.pos, (wall.width, wall.height), _wall.pos, (_wall.width, _wall.height)):
                    if Collision.sat(wall.get_abs_vertices(), _wall.get_abs_vertices()):
                        logger_hiding.info(f"\tCouldn't add Wall #{self.walls_counter + 1}, because it would overlap with other Wall.")
                        can_create = False
                        break
            if enemy and Collision.aabb(enemy.pos, (enemy.width, enemy.height), wall.pos, (wall.width, wall.height)):
                if Collision.sat(self.get_abs_vertices(), enemy.get_abs_vertices()):
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
        """
        Takes and performs the action

        Parameters
        ----------
            local_env : dict
                contains Player Local Environment
            walls_group : list of hidenseek.objects.fixes.Wall
                contains all walls in the area
                TODO: Once Agent POV done - REPLACE WITH local_env['walls']
        
        Returns
        -------
            None
        """
        new_action = copy.deepcopy(random.choice(self.actions))

        if new_action['type'] == 'NOOP':
           logger_hiding.info("NOOP! NOOP!")
        elif new_action['type'] == 'movement':
            x = math.cos(self.direction) * self.velocity * self.speed
            y = math.sin(self.direction) * self.velocity * self.speed
            old_pos = copy.deepcopy(self.pos)
            new_pos = self.pos + Point((x,y))
            logger_hiding.info(f"Moving to {new_pos}")

            logger_hiding.info(f"\tChecking collisions with other Objects")

            for wall in local_env['walls']:
                if Collision.aabb(new_pos, (self.width, self.height), wall.pos, (wall.width, wall.height)):
                    self.move_action(new_pos)
                    if Collision.sat(self.get_abs_vertices(), wall.get_abs_vertices()):
                        logger_hiding.info("\tCollision with some Wall! Not moving anywhere")
                        self.move_action(old_pos)
                        return

            self.move_action(new_pos)
        elif new_action['type'] == 'rotation':
            self.rotate(new_action['content'])
        elif new_action['type'] == 'add_wall':
            self.add_wall(walls_group, local_env['enemy'])

    def __str__(self):
        return "[Hiding Agent]"


class Seeker(Player):
    """
    Child Seeker Class for Hide'n'Seek Game, inherits from Player.

    Attributes
    ----------
        width : int
            width of the Player Rectangle
        height : int
            height of the Player Rectangle
        SCREEN_WIDTH : int
            width of the game window
        SCREEN_HEIGHT : int
            height of the game window
        pos : hidenseek.ext.supportive.Point
            object position on the game display
        speed : float
            speed ratio for Player movement
        velocity : float
            velocity ratio for Player movement, calculated by using Game Engine FPS Lock value
        vision : pygame.Rect
            Player POV
            TODO: Probably will be standalone Object after implementing proper POV
        image_index : int
            determines which image should be drawn
        images : list of pygame.Surface
            objects with sprite/images from which the proper one will be drawn
        image : pygame.Surface
            object with sprite/image, chosen by 'image_index'
        rect : pygame.Rect
            object Rectangle, to be drawn
        polygon_points : list of tuples
            vertices, used for collision check in SAT
        actions : list of dict
            contains all possible Player actions

    Methods
    -------
        get_abs_vertices():
            returns absolute vertices coordinates (in game screen coordinates system)
        move_action(new_pos):
            algorithm which moves the Player object to given poisition
        remove_wall(wall, walls_group):
            creates new hidenseek.objects.fixes.Wall object and adds it to the game if no collision
        update(local_env, walls_group):
            takes and performs the action
    """
    
    def __init__(self, width, height, speed, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT, color_anim):
        """
        Constructs all neccesary attributes for the Seeker Object

        Parameters
        ----------
            width : int
                width of the Player Rectangle
            height : int
                height of the Player Rectangle
            speed : float
                speed ratio for Player movement
            pos_ratio : tuple
                used to calculate initial position of the Player in absolute coordinate system (game screen)
            color : tuple
                if no image, represents the shape fill color in RGB format, i.e. (0, 0, 0)
                TODO: ONCE USING IMAGE - DELETE THIS
            SCREEN_WIDTH : int
                width of the game window
            SCREEN_HEIGHT : int
                height of the game window
            color_anim : tuple
                if no image, represents the shape fill color for animation in RGB format, i.e. (0, 0, 0)
                TODO: ONCE USING IMAGE - DELETE THIS
        """

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
        """
        Removes the Wall if in radius and lowers the Wall counter for the Wall owner

        Parameters
        ----------
            wall : hidenseek.objects.fixed.Wall
                hidenseek.objects.fixed.Wall object to delete
            walls_group : list of hidenseek.objects.fixes.Wall
                contains all walls in the area
                TODO: Once Agent POV done - REPLACE WITH local_env['walls']
        
        Returns
        -------
            None
        """

        logger_seeker.info(f"Removed wall {wall.pos}")
        walls_group.remove(wall)
        wall.owner.walls_counter -= 1
        del wall

    def update(self, local_env, walls_group):
        """
        Takes and performs the action

        Parameters
        ----------
            local_env : dict
                contains Player Local Environment
            walls_group : list of hidenseek.objects.fixes.Wall
                contains all walls in the area
                TODO: Once Agent POV done - REPLACE WITH local_env['walls']
        
        Returns
        -------
            None
        """

        new_action = copy.deepcopy(random.choice(self.actions))

        if new_action['type'] == 'NOOP':
            logger_seeker.info("NOOP! NOOP!")
        elif new_action['type'] == 'movement':
            x = math.cos(self.direction) * self.velocity * self.speed
            y = math.sin(self.direction) * self.velocity * self.speed
            old_pos = copy.deepcopy(self.pos)
            new_pos = self.pos + Point((x,y))
            logger_hiding.info(f"Moving to {new_pos}")

            logger_hiding.info(f"\tChecking collisions with other Objects")

            for wall in local_env['walls']:
                if Collision.aabb(new_pos, (self.width, self.height), wall.pos, (wall.width, wall.height)):
                    self.move_action(new_pos)
                    if Collision.sat(self.get_abs_vertices(), wall.get_abs_vertices()):
                        logger_hiding.info("\tCollision with some Wall! Not moving anywhere")
                        self.move_action(old_pos)
                        return

            self.move_action(new_pos)
        elif new_action['type'] == 'rotation':
            self.rotate(new_action['content'])

        elif new_action['type'] == 'remove_wall':
            if local_env['walls']:
                new_action['content'] = random.choice(local_env['walls'])
                self.remove_wall(new_action['content'], walls_group)
            else:
                logger_seeker.info(f"No Wall to remove, doing... nothing.")
        
    def __str__(self):
        return "[Seeker]"
