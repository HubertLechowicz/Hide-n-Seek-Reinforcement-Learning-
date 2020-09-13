import pygame
from hidenseek_gym.supportive import Point, Collision
from hidenseek_gym.fixed import Wall
import copy
import random
import json
import math
import numpy as np

WALL_TIMER = 5


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
        wall_timer : float
            cooldown (in seconds) for any wall-specific action
        vision : pygame.Rect
            Player POV
        ray_objects : list of Objects (3-el or 4-el list of Point or)
            Player Ray POV
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
    def __init__(self, display, cfg, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT, color_anim=(64, 128, 240)):
        """
        Constructs all neccesary attributes for the Player Object

        Parameters
        ----------
            cfg : configparser Object
                Agent Config Object
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
        print(f"Self: {self}")
        print(f"Display: {display}")
        print(f"Config: {cfg}")
        print(f"Pos Ratio: {pos_ratio}")
        print(f"Color: {color}")
        print(f"S_W: {SCREEN_WIDTH}")
        print(f"S_H: {SCREEN_HEIGHT}")
        print(f"Color ANim: {color_anim}")
        self.width = cfg.getint('WIDTH', fallback=50)
        self.height = cfg.getint('HEIGHT', fallback=50)

        self.pos_init = Point(
            (pos_ratio[0] * SCREEN_WIDTH, pos_ratio[1] * SCREEN_HEIGHT))
        self.pos = Point(
            (pos_ratio[0] * SCREEN_WIDTH, pos_ratio[1] * SCREEN_HEIGHT))

        self.SCREEN_WIDTH = SCREEN_WIDTH
        self.SCREEN_HEIGHT = SCREEN_HEIGHT

        self.speed = cfg.getfloat('SPEED_RATIO', fallback=30.0)
        self.velocity = 0
        self.wall_timer = WALL_TIMER

        self.vision_top = None
        self.ray_objects = None
        self.vision_rad = math.pi

        self.image_index = 0
        self.direction = 0  # radians from which vision_rad is added/substracted
        self.color = color  # temp, until sprites
        self.color_anim = color_anim  # temp, until sprites

        self.polygon_points = [
            (self.width - 10, self.height / 2),
            (.4 * self.width, self.height - 5),
            (.4 * self.width, 5),
        ]

        image_inplace = pygame.Surface((self.width, self.height))
        image_inplace.set_colorkey((0, 0, 0))
        pygame.draw.polygon(image_inplace, self.color, self.polygon_points)
        pygame.draw.rect(image_inplace, (255, 255, 255),
                         pygame.Rect(0, 0, self.width, self.height), 1)

        image_movement = pygame.Surface((self.width, self.height))
        image_movement.set_colorkey((0, 0, 0))
        pygame.draw.polygon(image_movement, self.color_anim,
                            self.polygon_points)
        pygame.draw.rect(image_movement, (255, 255, 255),
                         pygame.Rect(0, 0, self.width, self.height), 1)
        self.polygon_points = [Point(polygon_point)
                               for polygon_point in self.polygon_points]

        self.images = [image_inplace] + \
            [image_movement for _ in range(10)]  # animations
        self.image = image_inplace
        self.rect = self.image.get_rect()
        self.rect.center = (self.pos_init.x, self.pos_init.y)

        self.vision = pygame.draw.arc(display, (0, 255, 255), self.rect.inflate(
            self.height * 3, self.width * 3), -self.direction - self.vision_rad / 2, -self.direction + self.vision_rad / 2, 1)

        # base class Player actions
        self.actions = [
            {
                'type': 'NOOP',  # do nothing
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

    def rotate(self, turn, local_env):
        """
        Rotates the object, accrodingly to the value, along it's axis.

        Parameters
        ----------
            turn : int, [-1,1]
                in which direction should agent rotate (clockwise or counterclockwise)
            local_env : dict
                contains Player Local Environment

        Returns
        -------
            None
        """
        old_direction = copy.deepcopy(self.direction)
        self.direction += self.velocity * turn * 10
        # base 2PI, because it's circle
        self.direction = self.direction % (2 * math.pi)

        angle = (self.direction - old_direction)

        # Update the polygon points for collisions
        old_polygon_points = copy.deepcopy(self.polygon_points)
        self.polygon_points = [Point.triangle_unit_circle_relative(
            angle, Point((self.width / 2, self.height / 2)), polygon_point) for polygon_point in self.polygon_points]

        for wall in local_env['walls']:
            if Collision.aabb(self.pos, (self.width, self.height), wall.pos, (wall.width, wall.height)):
                if Collision.sat(self.get_abs_vertices(), wall.get_abs_vertices()):
                    self.polygon_points = old_polygon_points
                    self.direction = old_direction
                    break

        if local_env['enemy']:
            if Collision.aabb(self.pos, (self.width, self.height), local_env['enemy'].pos, (local_env['enemy'].width, local_env['enemy'].height)):
                if Collision.sat(self.get_abs_vertices(), local_env['enemy'].get_abs_vertices()):
                    self.polygon_points = old_polygon_points
                    self.direction = old_direction

        polygon_points_tuples = [(p.x, p.y) for p in self.polygon_points]
        image_inplace = pygame.Surface((self.width, self.height))
        image_inplace.set_colorkey((0, 0, 0))
        pygame.draw.polygon(image_inplace, self.color, polygon_points_tuples)
        pygame.draw.rect(image_inplace, (255, 255, 255),
                         pygame.Rect(0, 0, self.width, self.height), 1)

        image_movement = pygame.Surface((self.width, self.height))
        image_movement.set_colorkey((0, 0, 0))
        pygame.draw.polygon(image_movement, self.color_anim,
                            polygon_points_tuples)
        pygame.draw.rect(image_movement, (255, 255, 255),
                         pygame.Rect(0, 0, self.width, self.height), 1)

        self.images = [image_inplace] + \
            [image_movement for _ in range(10)]  # animations
        self.image = image_inplace

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

        return [Point((polygon_point.x + self.rect.left, polygon_point.y + self.rect.top)) for polygon_point in self.polygon_points]

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

        if old_pos != self.pos:  # if moving
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
        else:  # if not moving
            self.image_index = 0

        self.image = self.images[self.image_index]

    def update_vision(self, display, local_env):
        """
        Updates Agent Vision

        Parameters
        ----------

            display : pygame.display
                Game Display (Window)

            local_env : dict
                contains Player Local Environment

        Returns
        -------
            None
        """

        self.vision = pygame.draw.arc(display, (0, 255, 255), self.rect.inflate(
            self.height * 3, self.width * 3), -self.direction - self.vision_rad / 2, -self.direction + self.vision_rad / 2, 1)
        new_point = Point.triangle_unit_circle(
            self.direction, side_size=self.width * 2)
        self.vision_top = self.pos + new_point

        pygame.draw.line(display, (0, 255, 0), (self.pos.x,
                                                self.pos.y), (self.vision_top.x, self.vision_top.y), 1)

        self.ray_points = []
        angles = np.linspace(0, self.vision_rad, num=int(
            int(self.vision_rad * 180 / math.pi) * 0.1), endpoint=True)  # clockwise
        for angle in angles[::-1]:  # counter-clockwise
            self.ray_point = Point.triangle_unit_circle_relative(
                angle, self.pos, self.pos + Point.triangle_unit_circle(self.direction - self.vision_rad / 2, side_size=self.width * 2))
            self.ray_points.append(self.ray_point)

        temp_ray_points = [Point(self.rect.center)]
        for vertex in self.ray_points:
            temp_ray_points.append(vertex)
            line_segment = [self.pos, vertex]  # first must me the center point
            vertex_new_point = False
            min_t_x = None
            try:
                for wall in local_env['walls']:
                    point, t_x = Collision.line_with_polygon(
                        line_segment, wall.get_abs_vertices(), min_t_x)
                    if point is None:
                        continue
                    if min_t_x is None:
                        min_t_x = t_x
                    if not vertex_new_point:
                        vertex_new_point = True
                        temp_ray_points[-1] = point
                    else:
                        temp_ray_points = temp_ray_points[:-1]
                        if min_t_x > t_x:
                            min_t_x = t_x
                            temp_ray_points[-1] = point
            except ZeroDivisionError:
                temp_ray_points = temp_ray_points[:-1]

            try:
                if local_env['enemy'] is not None:
                    point, t_x = Collision.line_with_polygon(
                        line_segment, local_env['enemy'].get_abs_vertices(), min_t_x)
                    if point is None:
                        continue
                    if min_t_x is None:
                        min_t_x = t_x
                    if not vertex_new_point:
                        vertex_new_point = True
                        temp_ray_points[-1] = point
                    else:
                        temp_ray_points = temp_ray_points[:-1]
                        if min_t_x > t_x:
                            min_t_x = t_x
                            temp_ray_points[-1] = point
            except ZeroDivisionError:
                temp_ray_points = temp_ray_points[:-1]

        for i in range(len(temp_ray_points)):
            start = (temp_ray_points[i].x, temp_ray_points[i].y)
            end = (temp_ray_points[(i + 1) % len(temp_ray_points)].x,
                   temp_ray_points[(i + 1) % len(temp_ray_points)].y)
            pygame.draw.line(display, (255, 0, 0), start, end)

        self.ray_objects = temp_ray_points

        self.ray_objects = Collision.triangulate_polygon(temp_ray_points)
        for obj in self.ray_objects:
            obj_len = len(obj)
            for i in range(obj_len):
                start = (obj[i].x, obj[i].y)
                end = (obj[(i + 1) % obj_len].x, obj[(i + 1) % obj_len].y)
                pygame.draw.line(display, (255, 85, 55), start, end)

        self.ray_objects.append([
            Point((self.rect.topleft)),
            Point((self.rect.topright)),
            Point((self.rect.bottomright)),
            Point((self.rect.bottomleft)),
        ])

    def update(self, local_env, walls_group):
        """
        Not implemented in Parent Class
        """
        raise NotImplementedError(
            "This is an abstract function of base class Player, please define it within class you created and make sure you don't use Player class.")


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
        wall_cfg : configparser Object
            Wall Config Object
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

    def __init__(self, display, cfg, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT, wall_cfg):
        """
        Constructs all neccesary attributes for the Hiding Object

        Parameters
        ----------
            cfg : configparser Object
                Hiding Agent Config
            pos_ratio : tuple
                used to calculate initial position of the Player in absolute coordinate system (game screen)
            color : tuple
                if no image, represents the shape fill color in RGB format, i.e. (0, 0, 0)
                TODO: ONCE USING IMAGE - DELETE THIS
            SCREEN_WIDTH : int
                width of the game window
            SCREEN_HEIGHT : int
                height of the game window
            wall_cfg : configparser Object
                Wall Config
        """

        super().__init__(display, cfg, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT)

        self.walls_counter = 0
        self.walls_max = cfg.getint('WALLS_MAX', fallback=5)
        self.wall_cfg = wall_cfg

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

        if self.walls_counter < self. walls_max:
            wall_pos = copy.deepcopy(self.vision_top)

            wall = Wall(self, self.wall_cfg, wall_pos.x, wall_pos.y)
            wall.rotate(self.direction, wall_pos)

            can_create = True
            for _wall in walls_group:
                if Collision.aabb(wall.pos, (wall.width, wall.height), _wall.pos, (_wall.width, _wall.height)):
                    if Collision.sat(wall.get_abs_vertices(), _wall.get_abs_vertices()):
                        can_create = False
                        break
            if enemy and Collision.aabb(enemy.pos, (enemy.width, enemy.height), wall.pos, (wall.width, wall.height)):
                if Collision.sat(self.get_abs_vertices(), enemy.get_abs_vertices()):
                    can_create = False

            if can_create:
                self.walls_counter += 1
                walls_group.add(wall)
            else:
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

        if self.wall_timer > 0:
            self.wall_timer -= self.velocity
        # for negative it's 0, for positive - higher than 0
        self.wall_timer = max(self.wall_timer, 0.)

        if new_action['type'] == 'NOOP':
            self.image_index = 0
            self.image = self.images[self.image_index]
        elif new_action['type'] == 'movement':
            x = math.cos(self.direction) * self.velocity * self.speed
            y = math.sin(self.direction) * self.velocity * self.speed
            old_pos = copy.deepcopy(self.pos)
            new_pos = self.pos + Point((x, y))

            for wall in local_env['walls']:
                if Collision.aabb(new_pos, (self.width, self.height), wall.pos, (wall.width, wall.height)):
                    self.move_action(new_pos)
                    if Collision.sat(self.get_abs_vertices(), wall.get_abs_vertices()):
                        self.move_action(old_pos)
                        return

            self.move_action(new_pos)
        elif new_action['type'] == 'rotation':
            self.rotate(new_action['content'], local_env)
        elif new_action['type'] == 'add_wall':
            if not self.wall_timer:  # if no cooldown
                self.add_wall(walls_group, local_env['enemy'])
                self.wall_timer = WALL_TIMER

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

    def __init__(self, display, cfg, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT, color_anim):
        """
        Constructs all neccesary attributes for the Seeker Object

        Parameters
        ----------
            cfg : configparser Object
                Seeker Agent Config
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

        super().__init__(display, cfg, pos_ratio, color,
                         SCREEN_WIDTH, SCREEN_HEIGHT, color_anim)

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

        if self.wall_timer > 0:
            self.wall_timer -= self.velocity
        # for negative it's 0, for positive - higher than 0
        self.wall_timer = max(self.wall_timer, 0.)

        if new_action['type'] == 'NOOP':
            self.image_index = 0
            self.image = self.images[self.image_index]
        elif new_action['type'] == 'movement':
            x = math.cos(self.direction) * self.velocity * self.speed
            y = math.sin(self.direction) * self.velocity * self.speed
            old_pos = copy.deepcopy(self.pos)
            new_pos = self.pos + Point((x, y))

            for wall in local_env['walls']:
                if Collision.aabb(new_pos, (self.width, self.height), wall.pos, (wall.width, wall.height)):
                    self.move_action(new_pos)
                    if Collision.sat(self.get_abs_vertices(), wall.get_abs_vertices()):
                        self.move_action(old_pos)
                        return

            self.move_action(new_pos)
        elif new_action['type'] == 'rotation':
            self.rotate(new_action['content'], local_env)

        elif new_action['type'] == 'remove_wall':

            if local_env['walls']:
                if not self.wall_timer:  # if no cooldown
                    new_action['content'] = random.choice(local_env['walls'])
                    self.remove_wall(new_action['content'], walls_group)
                    self.wall_timer = WALL_TIMER

    def __str__(self):
        return "[Seeker]"
