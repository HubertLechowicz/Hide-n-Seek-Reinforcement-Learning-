import pygame
import math
from PIL import Image


class Point():
    """
    Point class, which corrensponds to a point on the coordinate system

    Attributes
    ----------
        x : float
        y : float

    Methods
    -------
        round(n):
            rounds Objects x & y to the 'n' decimal place, default: 0 (integer)
        orthogonally():
            returns tuple which contains orthogonal representation of Point
        det(obj):
            return determinant of caller and argument Point considered as matrixes
        dot(obj):
            returns dot product between caller and argument Point
        distance(obj):
            returns cartesian distance between caller and argument Point
        square():
            returns Point square representation (x^2 + y^2)

        @staticmethod
        triangle_unit_circle(radians, side_size):
            returns point moved by Radians distant by Side_size in terms of (0, 0) game screen

        @staticmethod
        triangle_unit_circle_relative(radians, center, target):
            returns Target point moved by Radians in terms of center Point
    """

    def __init__(self, position):
        self.x, self.y = position

    def __add__(self, obj):
        """
        Adds Point to the 'Point', 'int' or 'float'
            Point - adding x & y separately
            int/float - adding one int/float to x & y

        Parameters
        ----------
            obj : hidenseek.ext.supportive.Point, int, float

        Returns
        -------
            Point : hidenseek.ext.supportive.Point
                new Point object
        """

        if isinstance(obj, Point):
            return Point((self.x + obj.x, self.y + obj.y))
        elif isinstance(obj, int) or isinstance(obj, float):
            return Point((self.x + obj, self.y + obj))
        else:
            raise TypeError(
                "You can only add Point to the 'Point', 'Integer' and 'Float' value types")

    def __sub__(self, obj):
        """
        Subs 'Point', 'int' or 'float' from the Point
            Point - subs x & y separately
            int/float - subs one int/float from x & y

        Parameters
        ----------
            obj : hidenseek.ext.supportive.Point, int, float

        Returns
        -------
            Point : hidenseek.ext.supportive.Point
                new Point object
        """

        if isinstance(obj, Point):
            return Point((self.x - obj.x, self.y - obj.y))
        elif isinstance(obj, int) or isinstance(obj, float):
            return Point((self.x - obj, self.y - obj))
        else:
            raise TypeError(
                "You can only sub Point with 'Point', 'Integer' and 'Float' value types")

    def __eq__(self, obj):
        if isinstance(obj, Point):
            return self.x == obj.x and self.y == obj.y
        else:
            return TypeError("You can compare only 2 'Point' variables")

    def __mul__(self, obj):
        """
        Multiplies Point by 'int' or 'float'

        Parameters
        ----------
            obj : int, float

        Returns
        -------
            Point : hidenseek.ext.supportive.Point
                new Point object
        """

        if not (isinstance(obj, int) or isinstance(obj, float)):
            raise TypeError(
                "You can only multiply Point by using 'Integer' or 'Float'")
        return Point((self.x * obj, self.y * obj))

    def __rmul__(self, obj):
        """
        Multiplies 'int' or 'float' with Point

        Parameters
        ----------
            obj : int, float

        Returns
        -------
            Point : hidenseek.ext.supportive.Point
                new Point object
        """

        return self.__mul__(obj)

    def __str__(self):
        return "Point( " + str(self.x) + ' , ' + str(self.y) + ' )'

    def __repr__(self):
        return self.__str__()

    def __truediv__(self, obj):
        """
        Divides Point by 'int' or 'float'

        Parameters
        ----------
            obj : int, float

        Returns
        -------
            Point : hidenseek.ext.supportive.Point
                new Point object
        """

        if not (isinstance(obj, int) or isinstance(obj, float)):
            raise TypeError(
                "You can only divide Point by using 'Integer' or 'Float'")
        return Point((self.x / obj, self.y / obj))

    def round(self, n=0):
        """
        Rounds Point x, y parameters to the given 'n' decimal point

        Parameters
        ----------
            n : int
                decides to which decimal point 'x' and 'y' should be rounded, default: 0

        Returns
        -------
            Point : hidenseek.ext.supportive.Point
                new Point object
        """

        return Point((round(self.x, n), round(self.y, n)))

    def orthogonally(self):
        """
        Returns orthogonal representation of Point

        Parameters
        ----------
            None

        Returns
        -------
            Point : tuple
                (y, -x)
        """

        return (self.y, -self.x)

    def det(self, obj):
        """
        return determinant of caller and argument Point considered as matrixes

        Parameters
        ----------
            obj : Point
                second Point needed to do the operation

        Returns
        -------
            det : float
                calculated determinant value
        """

        return self.x * obj.y - self.y * obj.x

    def distance(self, obj):
        """
        return Cartesian Distance between caller and argument Point considered as matrixes

        Parameters
        ----------
            obj : Point
                second Point needed to do the operation

        Returns
        -------
            cart_dist : float
                Cartesian Distance between 2 Points
        """
        return round(math.sqrt((obj.x - self.x)**2 + (obj.y - self.y)**2), 4)

    def dot(self, obj):
        """
        return dot product between caller and argument Point considered as matrixes

        Parameters
        ----------
            obj : Point
                second Point needed to do the operation

        Returns
        -------
            dot : float
                calculated dot product
        """
        return self.x * obj.x + self.y * obj.y

    def square(self):
        """
        returns Point square representation (x^2 + y^2)

        Parameters
        ----------
            obj : Point
                second Point needed to do the operation

        Returns
        -------
            square : float
                calculated Point square value
        """
        return self.x * self.x + self.y * self.y

    @staticmethod
    def triangle_unit_circle(radians, side_size):
        """
        Calculates relocation/movement in absolute coordinate system (display) based on radians

        Parameters
        ----------
            radians : float
                Movement angle in radians
            side_size : float
                Width or Height value, depending on the axes (x = width, y = height)

        Returns
        -------
            Point : hidenseek.ext.supportive.Point
                Relocation/movement in absolute coordinate system
        """

        x = math.cos(radians) * side_size
        y = math.sin(radians) * side_size

        return Point((x, y))

    @staticmethod
    def triangle_unit_circle_relative(radians, center, target):
        """
        Calculates relocation/movement in relative coordinate system (i.e. Rectangle) based on radians

        Parameters
        ----------
            radians : float
                Movement angle in radians
            center : Point
                Center of the Relative Object (i.e. Rectangle)
            target : Point
                Target Point moving around the center

        Returns
        -------
            Point : hidenseek.ext.supportive.Point
                Relocation/movement in relative coordinate system
        """

        dist_axes = target - center

        x = center.x + math.cos(radians) * dist_axes.x - \
            math.sin(radians) * dist_axes.y
        y = center.y + math.sin(radians) * dist_axes.x + \
            math.cos(radians) * dist_axes.y

        return Point((x, y))


class Collision:
    """
    Static Collision class, basically Collision Detection System

    Attributes
    ----------
        None

    Methods
    -------
        @staticmethod
        aabb(r1, r1_size, r2_, r2_size):
            returns collision by using Axis-Aligned Bounding Boxes method
        @staticmethod
        circle_with_rect(circle, rect):
            returns collision by using simple Circle with Rect Collision Check
        @staticmethod
        sat(vertices_obj1, vertices_obj2):
            returns collision by using Separating Axis Theorem
        @staticmethod
        find_intersection(segment1, segment2)
            if intersection between segment1 & segment2 exists, returns closes Point; if not - returns None
        @staticmethod
        get_objects_in_local_env(objs, center, radius, angle, vertices)
            returns list of objects (from argument objs) which are in given local environment
    """

    @staticmethod
    def aabb(r1, r1_size, r2, r2_size):
        """ 
        Uses Axis-Aligned Bounding Boxes method to determine if objects CAN collide. 
        It is 'certain' for rectangles, for Polygons it is a pre-selection to reduce computation time.

        Parameters
        ----------
            r1 : hidenseek.ext.supportive.Point
                center of rectangle
            r1_size : tuple
            r2 : hidenseek.ext.supportive.Point
                center of rectangle
            r2_size : tuple

        Returns
        -------
            aabb : bool
                returns if object 'r1' collides with object 'r2'
        """

        r1_w, r1_h = r1_size
        r2_w, r2_h = r2_size

        if r1.x + r1_w / 2 > r2.x - r2_w / 2 and r1.x - r1_w / 2 < r2.x + r2_w / 2 and r1.y - r1_h / 2 < r2.y + r2_h / 2 and r1.y + r1_h / 2 > r2.y - r2_h / 2:
            return True

        return False

    @staticmethod
    def circle_with_rect(circle, rect):
        """ 
        Uses simple Circle with Rectangle collision detection method to determine if objects collide. 

        Parameters
        ----------
            circle : pygame.Rect
            rect : pygame.Rect

        Returns
        -------
            circle_with_rect : bool
                returns if object 'circle' collides with object 'rect'
        """

        if not isinstance(circle, pygame.Rect):
            raise TypeError(
                f"Circle is not a pygame.Rect object. It is {type(circle)}. Make sure to use pygame.Rect class for Circle - Rect Collision Detector")
        if not isinstance(rect, pygame.Rect):
            raise TypeError(
                f"Rectangle is not a pygame.Rect object. It is {type(rect)}. Make sure to use pygame.Rect class for Circle - Rect Collision Detector")

        x = circle.center[0]
        y = circle.center[1]
        if x < rect.center[0]:
            if abs(x - rect.center[0]) < abs(x - rect.left):
                x = rect.center[0]
            else:
                x = rect.left
        elif x > rect.center[0]:
            if abs(x - rect.center[0]) < abs(x - rect.right):
                x = rect.center[0]
            else:
                x = rect.right

        if y < rect.center[1]:
            if abs(y - rect.center[1]) < abs(y - rect.top):
                y = rect.center[1]
            else:
                y = rect.top
        elif y > rect.center[1]:
            if abs(y - rect.center[1]) < abs(y - rect.bottom):
                y = rect.center[1]
            else:
                y = rect.bottom

        dist_x = circle.center[0] - x
        dist_y = circle.center[1] - y
        dist = dist_x**2 + dist_y**2

        if dist < (circle.width / 2)**2:
            return True

        return False

    @staticmethod
    def _normalize_point_tuple(point):
        """ 
        Normalizes input point

        Parameters
        ----------
            point : tuple

        Returns
        -------
            new_point : tuple
                returns normalized Point in tuple
        """

        norm = math.sqrt(point[0]**2 + point[1]**2)
        return (point[0] / norm, point[1] / norm)

    @staticmethod
    def _sat_project_to_axis(vertices, axis):
        """ 
        Projects vertices to axis

        Parameters
        ----------
            vertices : list
            axis : tuple

        Returns
        -------
            new_point : list
                returns area occupied by vertices projected to an axis
        """

        dots = [vertex.x * axis[0] + vertex.y * axis[1] for vertex in vertices]
        return [min(dots), max(dots)]

    @staticmethod
    def _get_polygon_edges(vertices):
        """
        Makes edges from polygon verticies

        Parameters
        ----------
            vertices_: list
                list of vertices objects (hidenseek.ext.supportive.Point)
        Returns
        -------
            edges : list
                returns list of edges (hidenseek.ext.supportive.Point)
        """
        return [vertices[(i + 1) % len(vertices)] - vertices[i] for i in
                range(len(vertices))] if len(vertices) > 2 else [vertices[1] - vertices[0]]

    @staticmethod
    def sat(vertices_obj1, vertices_obj2):
        """ 
        Checks if 2 objects collide by using Separating Axis Theorem

        Parameters
        ----------
            vertices_obj1 : list
                list of vertices objects (hidenseek.ext.supportive.Point) for first object
            vertices_obj2 : list
                list of vertices objects (hidenseek.ext.supportive.Point) for second object

        Returns
        -------
            collide : bool
                returns if objects collide
        """
        # edges function
        edges_1 = Collision._get_polygon_edges(vertices_obj1)
        edges_2 = Collision._get_polygon_edges(vertices_obj2)

        # all edges
        edges = edges_1 + edges_2

        # axes
        axes = [Collision._normalize_point_tuple(
            edge.orthogonally()) for edge in edges]
        for axis in axes:
            projection_1 = Collision._sat_project_to_axis(vertices_obj1, axis)
            projection_2 = Collision._sat_project_to_axis(vertices_obj2, axis)

            if (
                not projection_2[0] <= projection_1[0] <= projection_2[1]
                and not projection_2[0] <= projection_1[1] <= projection_2[1]
                and not projection_1[0] <= projection_2[0] <= projection_1[1]
                and not projection_1[0] <= projection_2[1] <= projection_1[1]
            ):
                return False

        return True

    @staticmethod
    def _find_slope(segment):
        """
        Return the slope of the line segment, if it is defined. If it is
        undefined, return None.
        """
        p1, p2 = segment[0], segment[1]
        if p2.x - p1.x == 0.0:
            return None
        else:
            return (p2.y - p1.y) / (p2.x-p1.x)

    @staticmethod
    def _find_y_intercept(slope, point):
        """
        Return the y-intercept of an infinite line with slope equal to slope that
        passes through point. If slope does not exist, return None.
        """
        if slope is None:
            return None
        else:
            return point.y - slope * point.x

    @staticmethod
    def _order_segment(segment):
        """
        Order endpoints in segment primarily by x position, and secondarily by y
        position.
        """
        ep1, ep2 = segment[0], segment[1]
        if (ep1.x > ep2.x or ep1.x == ep2.x and ep1.y > ep2.y):
            segment[0], segment[1] = segment[1], segment[0]

    @staticmethod
    def _order_segments(segments):
        """
        Order segments by each segment's first endpoint. Similar to order_segment,
        order primarily by first endpoint's x position, and secondarily by first
        endpoint's y position.
        """
        seg1, seg2 = segments
        if (seg1[0].x > seg2[0].x or seg1[0].x == seg2[0].x
                and seg1[0].y > seg2[0].y):
            segments[0], segments[1] = segments[1], segments[0]

    @staticmethod
    def _on(point, segment):
        """
        Return True if point lies on segment. Otherwise, return False.
        """
        return (Collision._within(segment[0].x, point.x, segment[1].x) and
                Collision._within(segment[0].y, point.y, segment[1].y))

    @staticmethod
    def _within(p, q, r):
        """
        Return True if q is between p and r. Otherwise, return False.
        """
        return p <= q <= r or r <= q <= p

    @staticmethod
    def find_intersection(segment1, segment2):
        """
        Return an intersection point of segment1 and segment2, if one exists. If
        multiple points of intersection exist, randomly return one of those
        intersection points. If no intersection exists, return None.

        Parameters
        ----------
            segment1 : [hidenseek.ext.supportive.Point, hidenseek.ext.supportive.Point]
                first segment to check intersection with
            segment2: [hidenseek.ext.supportive.Point, hidenseek.ext.supportive.Point]
                second segment to check intersection with
        Returns
        -------
            intersect_point : Point or None
                if intersection exists, returns the Point object; else None
        """
        [s1, s2] = [Collision._find_slope(l) for l in [segment1, segment2]]
        [k1, k2] = [Collision._find_y_intercept(s, l[0])
                    for s, l in [(s1, segment1), (s2, segment2)]]

        if s1 == s2:
            if k1 != k2:
                return None
            #  at this point, the two line segments are known to lie on the same
            #  infinite line (i.e. all of the endpoints are collinear)
            segments = [segment1, segment2]
            for segment in segments:
                Collision._order_segment(segment)
            Collision._order_segments(segments)
            intersection = segments[1][0]
        else:
            #  assume segment 1 has slope and segment 2 doesn't
            s, x, k = s1, segment2[0].x, k1
            #  assumption wrong, segment 1 doesn't have a slope, but segment 2 does
            if s1 is None:
                s, x, k = s2, segment1[0].x, k2
            #  assumption wrong, segments 1 and 2 both have slopes
            elif s2 is not None:
                x = (k2-k1) / (s1-s2)
            y = s*x + k
            intersection = Point((x, y)).round(4)

        if Collision._on(intersection, segment1) and Collision._on(intersection, segment2):
            return intersection

        return None

    @staticmethod
    def get_objects_in_local_env(objs, center, radius, angle, vertices):
        """
        Checks if objects are in Local Environment

        Parameters
        ----------
            objs : list of pygame.Rect
                objects to check if in local
            center : pygame.Rect
                local environment source (i.e. Agent) center
            radius : int
                local environment source (i.e. Agent) vision radius
            angle : int
                local environment source (i.e. Agent) direction [radians]
            vertices : list of tuples
                list of Agent POV vertices

        Returns
        -------
            in_radius : list
                list of pygame.Rect objects being in Local Environment
        """

        in_radius = []
        # width, height for arc w/ 0 radians, don't need an actual arc
        arc_surface = pygame.Surface((radius, 2 * radius))
        arc_surface = pygame.transform.rotozoom(
            arc_surface, -angle*180/math.pi, 1)

        # Create a new rect with the center of the sprite.
        arc_rect = arc_surface.get_rect()
        arc_center = Point.triangle_unit_circle_relative(
            angle, center, Point((center.x + radius / 2, center.y)))
        arc_rect.center = (arc_center.x, arc_center.y)

        for obj in objs:
            if Collision.aabb(arc_center, arc_rect.size, obj.pos, (obj.width, obj.height)):
                for vertices_obj in vertices:
                    if Collision.sat(obj.get_abs_vertices(), vertices_obj):
                        in_radius.append(obj)
                        break

        return in_radius


class MapGenerator:
    """
    Map Generator class, creating map form a picture

    Attributes
    ----------
        None

    Methods
    -------
        @staticmethod
        open_bmp(filename):
            returns map from bmp
        @staticmethod
        isnt_in_object(list_objects, x, y):
            returns information if point isn't in object
        @staticmethod
        get_objects_coordinates(map, palette):
            returns objects with their types and positions
        @staticmethod
        get_predefined_palette()
            returns dictionary of types of objects and their colors
        @staticmethod
        searcher(x1, y1, objects, map)
            returns the last point from figure
    """
    @staticmethod
    def open_bmp(filename):
        """
        Opens and returns map

        Parameters
        ----------
            filename :
        Returns
        -------
            intersect_point : Point or None
                if intersection exists, returns the Point object; else None
        """
        map_in_bmp = Image.open(filename)
        return map_in_bmp

    @staticmethod
    def isnt_in_object(list_objects, x, y):
        if (len(list_objects) == 0):
            return True

        for objects in list_objects:
            if (x >= objects["vertices"][0]["x"]):
                if (x <= objects["vertices"][1]["x"]):
                    if (y >= objects["vertices"][0]["y"]):
                        if (y <= objects["vertices"][1]["y"]):
                            return False
        return True

    @staticmethod
    def get_objects_coordinates(map, palette):
        objects = []

        for x in range(0, map.size[0], 1):
            for y in range(0, map.size[1], 1):
                if (MapGenerator.isnt_in_object(objects, x, y)):
                    this_pixel = map.getpixel((x, y))[0:3]
                    if (this_pixel != (255, 255, 255)):
                        tmp_coordinates = MapGenerator.searcher(
                            x, y, objects, map)
                        tmp_object = {
                            "type": palette['#%02x%02x%02x' % this_pixel],
                            "vertices": [
                                {
                                    "x": x,
                                    "y": y
                                },
                                {
                                    "x": tmp_coordinates[0],
                                    "y": tmp_coordinates[1]
                                }
                            ]
                        }
                        objects.append(tmp_object)
        return objects

    @staticmethod
    def get_predefined_palette():
        return {
            # colors
            # white - background
            "#ffffff": "background",

            # black - wall
            "#000000": "wall",

            "#0000ff": "hider",  # dark blue
            "#ff0000": "seeker",  # red

            "#00ff00": "bushes",  # green
            "#00ffff": "glass"  # light blue

        }

    @staticmethod
    def searcher(x1, y1, objects, map):
        x2 = x1
        y2 = y1
        color = map.getpixel((x1, y1))[0:3]

        # ===================
        # check x
        for x in range(x1 + 1, map.size[0], 1):
            if MapGenerator.isnt_in_object(objects, x, y1):
                if map.getpixel((x, y1))[0:3] == color:
                    x2 = x2 + 1
                else:
                    break
            else:
                break

        # ===================
        # check y
        ended = False
        for y in range(y1 + 1, map.size[1], 1):
            if ended:
                break
            for x in range(x1 + 1, x2, 1):
                if (MapGenerator.isnt_in_object(objects, x, y)):
                    if (map.getpixel((x, y))[0:3] != color):
                        ended = True
                        break
                else:
                    ended = True
                    break
            if (ended == False):
                y2 = y2 + 1
        return x2, y2
