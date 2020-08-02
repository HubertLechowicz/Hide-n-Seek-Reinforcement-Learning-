import pygame
import math

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
            raise TypeError("You can only add Point to the 'Point', 'Integer' and 'Float' value types")

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
            raise TypeError("You can only sub Point with 'Point', 'Integer' and 'Float' value types")

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
            raise TypeError("You can only multiply Point by using 'Integer' or 'Float'")
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

    @staticmethod
    def triangle_unit_circle(radians, **kwargs):
        """
        Calculates relocation/movement in absolute coordinate system (display) based on radians

        Parameters
        ----------
            radians : float
                Movement angle in radians
            side_size : float
                Width or Height value, depending on the axes (x = width, y = height), optional
            velocity : float
                Based on FPS value, increases/lowers movement, optional
            speed : float
                Based on Agent Speed Ratio, increases/lowers movement, optional

        Returns
        -------
            Point : hidenseek.ext.supportive.Point
                Relocation/movement in absolute coordinate system
        """

        x = math.cos(radians)
        y = math.sin(radians)

        if 'side_size' in kwargs:
            x *= kwargs['side_size']
            y *= kwargs['side_size']
        if 'velocity' in kwargs:
            x *= kwargs['velocity']
            y *= kwargs['velocity']
        if 'speed' in kwargs:
            x *= kwargs['speed']
            y *= kwargs['speed']

        return Point((x, y))


class Collision:
    """
    Static Collision class, basically Collision Detection System

    Attributes
    ----------
        None

    Methods
    -------
        aabb(r1, r1_size, r2_, r2_size):
            returns collision by using Axis-Aligned Bounding Boxes method
        circle_with_rect(circle, rect):
            returns collision by using simple Circle with Rect Collision Check
        normalize_point_tuple(point):
            normalizes point that is a tuple (not Point class)
        sat_project_to_axis(vertices, axis):
            projects Vertices to Axis
        sat(vertices_obj1, vertices_obj2):
            returns collision by using Separating Axis Theorem
    """

    @staticmethod
    def aabb(r1, r1_size, r2, r2_size):
        """ 
        Uses Axis-Aligned Bounding Boxes method to determine if objects CAN collide. 
        It is 'certain' for rectangles, for Polygons it is a pre-selection to reduce computation time.
        
        Parameters
        ----------
            r1 : hidenseek.ext.supportive.Point
            r1_size : tuple
            r2 : hidenseek.ext.supportive.Point
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
            raise TypeError(f"Circle is not a pygame.Rect object. It is {type(circle)}. Make sure to use pygame.Rect class for Circle - Rect Collision Detector")
        if not isinstance(rect, pygame.Rect):
            raise TypeError(f"Rectangle is not a pygame.Rect object. It is {type(rect)}. Make sure to use pygame.Rect class for Circle - Rect Collision Detector")
        
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
    def normalize_point_tuple(point):
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
    def sat_project_to_axis(vertices, axis):
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
        edges_1 = [vertices_obj1[(i + 1) % len(vertices_obj1)] - vertices_obj1[i] for i in range(len(vertices_obj1))]
        edges_2 = [vertices_obj2[(i + 1) % len(vertices_obj2)] - vertices_obj2[i] for i in range(len(vertices_obj2))]

        # all edges
        edges = edges_1 + edges_2

        # axes
        axes = [Collision.normalize_point_tuple(edge.orthogonally()) for edge in edges]
        for axis in axes:
            projection_1 = Collision.sat_project_to_axis(vertices_obj1, axis)
            projection_2 = Collision.sat_project_to_axis(vertices_obj2, axis)

            if not projection_2[0] <= projection_1[0] <= projection_2[1] and not projection_2[0] <= projection_1[1] <= projection_2[1] and not projection_1[0] <= projection_2[0] <= projection_1[1] and not projection_1[0] <= projection_2[1] <= projection_1[1]:
                return False

        return True