import pygame
from game_env.hidenseek_gym.supportive import Point, Collision
from game_env.hidenseek_gym.fixed import Wall
import copy
import random
import json
import math
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
        self.pos_init = pos_ratio

        self.SCREEN_WIDTH = SCREEN_WIDTH
        self.SCREEN_HEIGHT = SCREEN_HEIGHT

        self.cfg = cfg
        self.speed = cfg.getfloat('SPEED_RATIO', fallback=1.0)
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
            Point((self.width - 10, self.height / 2)),
            Point((.4 * self.width, self.height - 5)),
            Point((.4 * self.width, 5)),
        ]
        polygon_tuples = [(p.x, p.y) for p in self.polygon_points]

        image_inplace = pygame.Surface((self.width, self.height))
        image_inplace.set_colorkey((0, 0, 0))
        pygame.draw.polygon(image_inplace, self.color, polygon_tuples)

        image_movement = pygame.Surface((self.width, self.height))
        image_movement.set_colorkey((0, 0, 0))
        pygame.draw.polygon(image_movement, self.color_anim,
                            polygon_tuples)

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
                'type': 'movement',
                'content': -1,
            },
            {
                'type': 'movement',
                'content': 1,
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
            self.rect.center = (self.pos.x, self.pos.y)
        else:  # if not moving
            self.image_index = 0

        self.image = self.images[self.image_index]

    def _determine_new_ray_points(self, wall_edges):
        """
        Algorithm which calculates new possible ray points based on the current Agent Position and Agent Direction

        Parameters
        ----------
            None

        Returns
        -------
            ray_points : list of Point
                list of new, standard Ray Points
        """

        ray_points = []
        dir_t = self.direction - 2*math.pi if self.direction > math.pi else self.direction
        point_angle_0 = self.pos + Point((self.vision_radius, 0))
        angles = np.linspace(dir_t - self.vision_rad / 2, dir_t + self.vision_rad / 2, num=11,
                             endpoint=True)  # counter-clockwise
        angles_min, angles_max = min(angles), max(angles)

        for p in [pnt for wall_edge in wall_edges for pnt in wall_edge]:
            delta = p - self.pos
            theta_radians = math.atan2(delta.y, delta.x)

            # 3rd quartet (2nd in math, 3rd in Y being from top to bottom), fixes 2nd; from [-PI; PI] to [-2PI; 0]
            if angles_min < -math.pi and theta_radians > 0:
                theta_radians = theta_radians - 2*math.pi
            # 2nd quartet (3rd in math, 2nd in Y being from top to bottom), fixes 3rd; from [-PI; PI] to [0; 2PI]
            elif angles_max > math.pi and theta_radians < 0:
                theta_radians = theta_radians + 2*math.pi

            if theta_radians not in angles and theta_radians > angles_min and theta_radians < angles_max:
                angles = np.append(angles, theta_radians)
        angles = np.sort(angles)

        for angle in angles:
            ray_point = Point.triangle_unit_circle_relative(
                angle, self.pos, point_angle_0)
            ray_points.append(ray_point)

        return ray_points

    def reduce_wall_edges(self, walls):
        """
        Algorithm which reduces wall edges from 4 per Wall to only 2 (closest ones)

        Parameters
        ----------
            walls : list of Wall
                list of Walls in Agent Local Environment

        Returns
        -------
            proper_walls_lines : list of [Point, Point]
                list of closest wall edges
        """

        walls_lines = [[[wall.get_abs_vertices()[i % 4], wall.get_abs_vertices()[
            (i + 1) % 4]] for i in range(4)] for wall in walls]

        # get only closer parallel wall edge, reduces computation by half
        proper_walls_lines = []
        for wall_lines in walls_lines:
            if self.pos.distance(wall_lines[0][0] + (wall_lines[0][1] - wall_lines[0][0]) / 2) < self.pos.distance(wall_lines[2][0] + (wall_lines[2][1] - wall_lines[2][0]) / 2):
                proper_walls_lines.append(wall_lines[0])
            else:
                proper_walls_lines.append(wall_lines[2])

            if self.pos.distance(wall_lines[1][0] + (wall_lines[1][1] - wall_lines[1][0]) / 2) < self.pos.distance(wall_lines[3][0] + (wall_lines[3][1] - wall_lines[3][0]) / 2):
                proper_walls_lines.append(wall_lines[1])
            else:
                proper_walls_lines.append(wall_lines[3])
        return proper_walls_lines

    def _find_intersections(self, wall_edges):
        """
        Algorithm which looks for new Ray Points, which are closer to the Agent Center than radius-distance Ray Points

        Parameters
        ----------
            wall_edges : list of [Point, Point]
                list of Wall Edges in Agent Local Environment

        Returns
        -------
            temp_ray_points : list of Point
                list of new Ray Points
        """

        edges_bounding_boxes = [
            {
                'center': (edge[0] + edge[1]) / 2,
                'size': (abs(edge[1].x - edge[0].x), abs(edge[1].y - edge[0].y))
            } for edge in wall_edges
        ]

        temp_ray_points = [Point(self.rect.center)]
        for vertex in self.ray_points:
            # first must be the center point
            line_segment = [self.pos.round(4), vertex.round(4)]
            new_point = copy.deepcopy(vertex.round(4))
            new_point_dist = self.pos.distance(new_point)
            bounding_box = {
                'center': (line_segment[0] + line_segment[1]) / 2,
                'size': (abs(line_segment[1].x - line_segment[0].x), abs(line_segment[1].y - line_segment[0].y))
            }
            for edge, edge_bounding_box in zip(wall_edges, edges_bounding_boxes):
                if not Collision.aabb(bounding_box['center'], bounding_box['size'], edge_bounding_box['center'], edge_bounding_box['size']):
                    continue
                p = Collision.line_intersection(line_segment, edge)
                if p and self.pos.distance(p) <= new_point_dist:
                    new_point = p
                    new_point_dist = self.pos.distance(p)
            temp_ray_points.append(new_point)
        return temp_ray_points

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

        wall_edges = self.reduce_wall_edges(local_env['walls'])
        self.ray_points = self._determine_new_ray_points(
            wall_edges)

        # without center
        self.ray_points = self._find_intersections(wall_edges)[1:]

        # creates triangles
        self.ray_objects = [[self.pos, self.ray_points[i], self.ray_points[i + 1]]
                            for i in range(len(self.ray_points) - 1) if self.ray_points[i] != self.ray_points[i + 1]]

        # adds Agent Rectangle to Agent Ray Objects
        self.ray_objects.append([
            Point((self.rect.topleft)),
            Point((self.rect.topright)),
            Point((self.rect.bottomright)),
            Point((self.rect.bottomleft)),
        ])

    def update(self, new_action, local_env):
        """
        Takes and performs the action

        Parameters
        ----------
            new_action : dict
                action taken by Agent
            local_env : dict
                contains Player Local Environment

        Returns
        -------
            None
        """
        if new_action['type'] == 'NOOP':
            self.image_index = 0
            self.image = self.images[self.image_index]
        elif new_action['type'] == 'movement':
            x = math.cos(self.direction) * self.speed * new_action['content']
            y = math.sin(self.direction) * self.speed * new_action['content']
            old_pos = copy.deepcopy(self.pos)
            new_pos = self.pos + Point((x, y))

            for wall in local_env['walls']:
                if Collision.aabb(new_pos, (self.width, self.height), wall.pos, (wall.width, wall.height)):
                    self._move_action(new_pos)
                    if Collision.sat(self.get_abs_vertices(), wall.get_abs_vertices()):
                        self._move_action(old_pos)
                        return

            self._move_action(new_pos)
        elif new_action['type'] == 'rotation':
            self._rotate(new_action['content'], local_env)


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

        self.walls_counter = 0
        self.walls_max = cfg.getint('WALLS_MAX', fallback=5)

        self.actions += [
            {
                'type': 'add_wall',
            }
        ]

    def __str__(self):
        return "[Hiding Agent]"

    def copy(self):
        return Hiding(self.cfg, (self.width, self.height), self.pos_init, self.color, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)


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

        self.actions += [
            {
                'type': 'remove_wall',
            },
        ]

    def __str__(self):
        return "[Seeker]"

    def copy(self):
        return Seeker(self.cfg, (self.width, self.height), self.pos_init, self.color, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.color_anim)