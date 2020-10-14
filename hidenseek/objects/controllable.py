import pygame
from ext.supportive import Point, Collision
from objects.fixed import Wall
import copy
import random
import json
import math
from ext.loggers import LOGGING_DASHES, logger_seeker, logger_hiding
import numpy as np


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
        speed : int
            speed ratio for Player movement (in ticks)
        speed_rotate : float
            speed ratio for Player rotate
        wall_timer_init : int
            init cooldown (in frames) for any wall-specific action
        wall_timer : int
            cooldown (in frames)for any wall-specific action
        vision_radius : float
            Player POV radius
        vision_rad : float
            Player POV angle
        vision_top : Point
            Player Top POV Point
        ray_points : list of Point
            Player Ray POV in Points representation
        ray_objects : list of Objects (3-el list of Point)
            Player Ray POV in Triangles representation
        direction : float
            POV angle in radians (Z = 2 * PI)
        image_index : int
            determines which image should be drawn
        images : list of pygame.Surface
            objects with sprite/images from which the proper one will be drawn
        image : pygame.Surface
            object with sprite/image, chosen by 'image_index'
        rect : pygame.Rect
            object Rectangle, to be drawn
        polygon_points : list of tuples
            Agent vertices, used for collision check in SAT
        actions : list of dict
            contains all possible Player actions

    Methods
    -------
        _rotate(turn, local_env):
            rotates the object, accordingly to the value, along its axis
        get_abs_vertices():
            returns absolute vertices coordinates (in game screen coordinates system)
        _move_action(new_pos):
            algorithm which moves the Player object to given poisition
        update_vision(local_env):
            updates Agent POV
        update(local_env):
            Not implemented in Parent Class
    """

    # color_anim IS TEMPORARILY HERE, BECAUSE THERE ARE NO ANIMATION SPRITES, ONLY RECTANGLES WITH COLORS
    def __init__(self, cfg, size, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT, color_anim=(64, 128, 240)):
        """
        Constructs all neccesary attributes for the Player Object

        Parameters
        ----------
            cfg : configparser Object
                Agent Config Object
            size : tuple
                Agent size
            pos_ratio : tuple
                used to calculate initial position of the Player in absolute coordinate system (game screen);
                if value < 1 then it's ratio in percentage, otherwise it's coord
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
        self.width = size[0]
        self.height = size[1]

        tmp_pos = list(pos_ratio)
        if tmp_pos[0] < 1:
            tmp_pos[0] *= SCREEN_WIDTH

        if tmp_pos[1] < 1:
            tmp_pos[1] *= SCREEN_HEIGHT

        self.pos = Point(tmp_pos)

        self.SCREEN_WIDTH = SCREEN_WIDTH
        self.SCREEN_HEIGHT = SCREEN_HEIGHT

        self.speed = cfg.getint('SPEED_RATIO', fallback=30)
        self.speed_rotate = cfg.getfloat('SPEED_ROTATE_RATIO', fallback=0.1)
        self.wall_timer_init = cfg.getint('WALL_ACTION_TIMEOUT', fallback=5)
        self.wall_timer = cfg.getint('WALL_ACTION_TIMEOUT', fallback=5)

        self.vision_radius = self.width * 2
        self.vision_top = None
        self.ray_objects = None
        self.vision_rad = math.pi
        self.ray_points = []
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
        self.rect.center = (self.pos.x, self.pos.y)

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

    def _rotate(self, turn, local_env):
        """
        Rotates the object, accordingly to the value, along its axis.

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
        self.direction += self.speed_rotate * turn
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

    def _move_action(self, new_pos):
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
            # region  https://trello.com/c/VzyZ3CM2

            # TODO delete when map is implemented, and walls are on the sides.
            if self.pos.y - self.height / 2 <= 0:
                self.pos.y = self.height / 2

            elif self.pos.y + self.height / 2 >= self.SCREEN_HEIGHT:
                self.pos.y = self.SCREEN_HEIGHT - self.height / 2

            if self.pos.x - self.width / 2 <= 0:
                self.pos.x = self.width / 2

            elif self.pos.x + self.width / 2 >= self.SCREEN_WIDTH:
                self.pos.x = self.SCREEN_WIDTH - self.width / 2
            # endregion
            self.rect.center = (self.pos.x, self.pos.y)
        else:  # if not moving
            self.image_index = 0

        self.image = self.images[self.image_index]

    def update_vision(self, local_env):
        """
        Updates Agent Vision

        Parameters
        ----------
            local_env : dict
                contains Player Local Environment

        Returns
        -------
            None
        """
        new_point = Point.triangle_unit_circle(
            self.direction, side_size=self.vision_radius)
        self.vision_top = self.pos + new_point

        self.ray_points = []
        angles = np.linspace(0, self.vision_rad, num=int(
            int(self.vision_rad * 180 / math.pi) * (self.vision_radius / 2) / 100), endpoint=True)  # counter-clockwise
        for angle in angles:  # clockwise
            ray_point = Point.triangle_unit_circle_relative(
                angle, self.pos, self.pos + Point.triangle_unit_circle(self.direction - self.vision_rad / 2, side_size=self.vision_radius))
            self.ray_points.append(ray_point)

        walls_lines = [[[wall.get_abs_vertices()[i % 4], wall.get_abs_vertices()[(
            i + 1) % 4]] for i in range(4)] for wall in local_env['walls']]

        # get only closer parallel wall edge, reduces computation by half
        proper_walls_lines = []
        for wall_lines in walls_lines:
            proper_wall_lines = []
            if self.pos.distance(wall_lines[0][0] + (wall_lines[0][1] - wall_lines[0][0]) / 2) < self.pos.distance(wall_lines[2][0] + (wall_lines[2][1] - wall_lines[2][0]) / 2):
                proper_wall_lines.append(wall_lines[0])
            else:
                proper_wall_lines.append(wall_lines[2])

            if self.pos.distance(wall_lines[1][0] + (wall_lines[1][1] - wall_lines[1][0]) / 2) < self.pos.distance(wall_lines[3][0] + (wall_lines[3][1] - wall_lines[3][0]) / 2):
                proper_wall_lines.append(wall_lines[1])
            else:
                proper_wall_lines.append(wall_lines[3])
            proper_walls_lines.append(proper_wall_lines)

        temp_ray_points = [Point(self.rect.center)]
        for vertex in self.ray_points:
            temp_ray_points.append(vertex)
            # first must be the center point
            line_segment = [self.pos.round(4), vertex.round(4)]
            vertex_new_point = False
            min_t_x = None
            for wall_lines in proper_walls_lines:
                point2 = None
                for line in wall_lines:
                    p2 = Collision.find_intersection(line_segment, line)
                    if p2 and (not point2 or self.pos.distance(p2) < self.pos.distance(point2)) and self.pos.distance(p2) <= self.vision_radius:
                        point2 = p2
                if point2 is None:
                    continue
                t_x = self.pos.distance(point2)
                if min_t_x is None:
                    min_t_x = t_x
                if not vertex_new_point:
                    vertex_new_point = True
                    temp_ray_points[-1] = point2
                else:
                    if min_t_x > t_x:
                        min_t_x = t_x
                        temp_ray_points[-1] = point2

        self.ray_points = copy.deepcopy(temp_ray_points[1:])  # without center

        self.ray_objects = [[self.pos, self.ray_points[i], self.ray_points[i + 1]]
                            for i in range(len(self.ray_points) - 1)]

        # if no interruption, then triangle is made from 10 % of angles
        # if interruption - triangle every angle change
        new_ray_objects = []
        vision_top_distance = round(self.pos.distance(self.vision_top), 2)
        angles_perc_10 = round(len(angles) / 10)
        j = 0
        for i in range(len(self.ray_objects)):
            if j == angles_perc_10:
                new_ray_objects.append(
                    [self.pos, self.ray_objects[i - j][1], self.ray_objects[i - 1][2]])
                j = 0

            if round(self.ray_objects[i][0].distance(self.ray_objects[i][1]), 2) == vision_top_distance and round(self.ray_objects[i][0].distance(self.ray_objects[i][2]), 2) == vision_top_distance:
                j += 1
                continue
            if j > 0:
                new_ray_objects.append(
                    [self.pos, self.ray_objects[i - j][1], self.ray_objects[i - 1][2]])

            j = 0
            new_ray_objects.append(self.ray_objects[i])
        new_ray_objects.append(
            [self.pos, self.ray_objects[i - j - 1][1], self.ray_objects[i][2]])
        self.ray_objects = new_ray_objects

        self.ray_objects.append([
            Point((self.rect.topleft)),
            Point((self.rect.topright)),
            Point((self.rect.bottomright)),
            Point((self.rect.bottomleft)),
        ])

    def update(self, new_action, local_env):
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
        speed : int
            speed ratio for Player movement (in ticks)
        speed_rotate : float
            speed ratio for Player rotate
        wall_timer_init : int
            init cooldown (in frames) for any wall-specific action
        wall_timer : int
            cooldown (in frames)for any wall-specific action
        vision_radius : float
            Player POV radius
        vision_rad : float
            Player POV angle
        vision_top : Point
            Player Top POV Point
        ray_points : list of Point
            Player Ray POV in Points representation
        ray_objects : list of Objects (3-el list of Point)
            Player Ray POV in Triangles representation
        direction : float
            POV angle in radians (Z = 2 * PI)
        image_index : int
            determines which image should be drawn
        images : list of pygame.Surface
            objects with sprite/images from which the proper one will be drawn
        image : pygame.Surface
            object with sprite/image, chosen by 'image_index'
        rect : pygame.Rect
            object Rectangle, to be drawn
        polygon_points : list of tuples
            Agent vertices, used for collision check in SAT
        actions : list of dict
            contains all possible Player actions
        walls_counter : int
            existing hidenseek.objects.fixes.Wall objects made by Hiding Player
        walls_max : int
            maximum amount of existing hidenseek.objects.fixes.Wall objects that may be created by Hiding Player 

    Methods
    -------
        _rotate(turn, local_env):
            rotates the object, accordingly to the value, along its axis
        get_abs_vertices():
            returns absolute vertices coordinates (in game screen coordinates system)
        _move_action(new_pos):
            algorithm which moves the Player object to given poisition
        update_vision(local_env):
            updates Agent POV
        _add_wall(walls, enemy):
            creates new hidenseek.objects.fixes.Wall object and adds it to the game if no collision
        update(local_env):
            takes and performs the action
    """

    def __init__(self, cfg, size, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT):
        """
        Constructs all neccesary attributes for the Hiding Object

        Parameters
        ----------
            cfg : configparser Object
                Hiding Agent Config
            size : tuple
                Agent size
            pos_ratio : tuple
                used to calculate initial position of the Player in absolute coordinate system (game screen);
                if value < 1 then it's ratio in percentage, otherwise it's coord
            color : tuple
                if no image, represents the shape fill color in RGB format, i.e. (0, 0, 0)
                TODO: ONCE USING IMAGE - DELETE THIS
            SCREEN_WIDTH : int
                width of the game window
            SCREEN_HEIGHT : int
                height of the game window
        """

        super().__init__(cfg, size, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT)

        logger_hiding.info(
            f"{LOGGING_DASHES} Creating New Hiding Agent (probably new game) {LOGGING_DASHES} ")
        logger_hiding.info("Initializing object")
        logger_hiding.info(f"\tSize: {self.width}x{self.height}")
        logger_hiding.info(f"\tSpeed: {self.speed}")
        logger_hiding.info(f"\tSprite: ---PLACEHOLDER---")
        logger_hiding.info(f"\tSprite for Animation: ---PLACEHOLDER---")

        self.walls_counter = 0
        self.walls_max = cfg.getint('WALLS_MAX', fallback=5)
        logger_hiding.info(
            f"\tWalls/Max: {self.walls_counter}/{self.walls_max}")

        self.actions += [
            {
                'type': 'add_wall',
            }
        ]

    def update(self, new_action, local_env):
        """
        Takes and performs the action

        Parameters
        ----------
            local_env : dict
                contains Player Local Environment

        Returns
        -------
            new_wall : Wall or None
                returns new Wall object if action was 'add_wall' and it was possible to create new Wall, otherwise None
        """

        if new_action['type'] == 'NOOP':
            self.image_index = 0
            self.image = self.images[self.image_index]
            logger_hiding.info("NOOP! NOOP!")
        elif new_action['type'] == 'movement':
            x = math.cos(self.direction) * self.speed
            y = math.sin(self.direction) * self.speed
            old_pos = copy.deepcopy(self.pos)
            new_pos = self.pos + Point((x, y))
            logger_hiding.info(f"Moving to {new_pos}")

            logger_hiding.info(f"\tChecking collisions with other Objects")

            for wall in local_env['walls']:
                if Collision.aabb(new_pos, (self.width, self.height), wall.pos, (wall.width, wall.height)):
                    self._move_action(new_pos)
                    if Collision.sat(self.get_abs_vertices(), wall.get_abs_vertices()):
                        logger_hiding.info(
                            "\tCollision with some Wall! Not moving anywhere")
                        self._move_action(old_pos)
                        return

            self._move_action(new_pos)
        elif new_action['type'] == 'rotation':
            self._rotate(new_action['content'], local_env)

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
        speed : int
            speed ratio for Player movement (in ticks)
        speed_rotate : float
            speed ratio for Player rotate
        wall_timer_init : int
            init cooldown (in frames) for any wall-specific action
        wall_timer : int
            cooldown (in frames)for any wall-specific action
        vision_radius : float
            Player POV radius
        vision_rad : float
            Player POV angle
        vision_top : Point
            Player Top POV Point
        ray_points : list of Point
            Player Ray POV in Points representation
        ray_objects : list of Objects (3-el list of Point)
            Player Ray POV in Triangles representation
        direction : float
            POV angle in radians (Z = 2 * PI)
        image_index : int
            determines which image should be drawn
        images : list of pygame.Surface
            objects with sprite/images from which the proper one will be drawn
        image : pygame.Surface
            object with sprite/image, chosen by 'image_index'
        rect : pygame.Rect
            object Rectangle, to be drawn
        polygon_points : list of tuples
            Agent vertices, used for collision check in SAT
        actions : list of dict
            contains all possible Player actions

    Methods
    -------
        _rotate(turn, local_env):
            rotates the object, accordingly to the value, along its axis
        get_abs_vertices():
            returns absolute vertices coordinates (in game screen coordinates system)
        _move_action(new_pos):
            algorithm which moves the Player object to given poisition
        update_vision(local_env):
            updates Agent POV
        update(local_env):
            takes and performs the action
    """

    def __init__(self, cfg, size, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT, color_anim):
        """
        Constructs all neccesary attributes for the Seeker Object

        Parameters
        ----------
            cfg : configparser Object
                Seeker Agent Config
            size : tuple
                Agent size
            pos_ratio : tuple
                used to calculate initial position of the Player in absolute coordinate system (game screen);
                if value < 1 then it's ratio in percentage, otherwise it's coord
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

        super().__init__(cfg, size, pos_ratio, color,
                         SCREEN_WIDTH, SCREEN_HEIGHT, color_anim)

        logger_seeker.info(
            f"{LOGGING_DASHES} Creating New Seeker Agent (probably new game) {LOGGING_DASHES} ")
        logger_seeker.info("Initializing object")
        logger_seeker.info(f"\tSize: {self.width}x{self.height}")
        logger_seeker.info(f"\tSpeed: {self.speed}")
        logger_seeker.info(f"\tSprite: ---PLACEHOLDER---")
        logger_seeker.info(f"\tSprite for Animation: ---PLACEHOLDER---")

        self.actions += [
            {
                'type': 'remove_wall',
            },
        ]

    def update(self, new_action, local_env):
        """
        Takes and performs the action

        Parameters
        ----------
            local_env : dict
                contains Player Local Environment

        Returns
        -------
            delete_wall : Wall or None
                returns Wall object to delete if action was 'remove_wall' otherwise None
                TODO: new_action['type'] == 'remove wall' needs to be changed from random choice, to experience-based choice.
        """

        if new_action['type'] == 'NOOP':
            self.image_index = 0
            self.image = self.images[self.image_index]
            logger_seeker.info("NOOP! NOOP!")
        elif new_action['type'] == 'movement':
            x = math.cos(self.direction) * self.speed
            y = math.sin(self.direction) * self.speed
            old_pos = copy.deepcopy(self.pos)
            new_pos = self.pos + Point((x, y))
            logger_seeker.info(f"Moving to {new_pos}")

            logger_seeker.info(f"\tChecking collisions with other Objects")

            for wall in local_env['walls']:
                if Collision.aabb(new_pos, (self.width, self.height), wall.pos, (wall.width, wall.height)):
                    self._move_action(new_pos)
                    if Collision.sat(self.get_abs_vertices(), wall.get_abs_vertices()):
                        logger_seeker.info(
                            "\tCollision with some Wall! Not moving anywhere")
                        self._move_action(old_pos)
                        return

            self._move_action(new_pos)
        elif new_action['type'] == 'rotation':
            self._rotate(new_action['content'], local_env)

    def __str__(self):
        return "[Seeker]"
