import pygame
import math

class Point():
    def __init__(self, position):
        self.x, self.y = position

    def __add__(self, obj):
        if isinstance(obj, Point):
            return Point((self.x + obj.x, self.y + obj.y))
        elif isinstance(obj, int) or isinstance(obj, float):
            return Point((self.x + obj, self.y + obj))
        else:
            raise TypeError("You can only add Point to the 'Point', 'Integer' and 'Float' value types")

    def __sub__(self, obj):
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
        if not (isinstance(obj, int) or isinstance(obj, float)):
            raise TypeError("You can only multiply Point by using 'Integer' or 'Float'")
        return Point((self.x * obj, self.y * obj))

    def __rmul__(self, obj):
        return self.__mul__(obj)

    def __str__(self):
        return "Point( " + str(self.x) + ' , ' + str(self.y) + ' )'

    def round(self, n=0):
        return Point((round(self.x, n), round(self.y, n)))

    def orthogonally(self):
        return (self.y, -self.x)

class Collision:
    @staticmethod
    def aabb(r1, r1_size, r2, r2_size):
        """ Uses Axis-Aligned Bounding Boxes method to determine if objects CAN collide. 
        It is 'certain' for rectangles, for Polygons it is a pre-selection to reduce computation time."""
        r1_w, r1_h = r1_size
        r2_w, r2_h = r2_size

        if r1.x + r1_w / 2 > r2.x - r2_w / 2 and r1.x - r1_w / 2 < r2.x + r2_w / 2 and r1.y - r1_h / 2 < r2.y + r2_h / 2 and r1.y + r1_h / 2 > r2.y - r2_h / 2:
            return True

        return False

    @staticmethod
    def circle_with_rect(circle, rect):
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
        norm = math.sqrt(point[0]**2 + point[1]**2)
        return (point[0] / norm, point[1] / norm)

    @staticmethod
    def sat_project_to_axis(vertices, axis):
        """ Projects Vertices to Axis for Separating Axis Theorem ('sat' method)"""
        dots = [vertex.x * axis[0] + vertex.y * axis[1] for vertex in vertices]
        return [min(dots), max(dots)]

    @staticmethod
    def sat(vertices_obj1, vertices_obj2, SCREEN_WIDTH, SCREEN_HEIGHT):
        """ Separating Axis Theorem to detect complex polygon collision """
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