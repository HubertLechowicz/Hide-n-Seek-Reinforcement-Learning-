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