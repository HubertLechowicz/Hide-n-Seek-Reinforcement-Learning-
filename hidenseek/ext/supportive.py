class Point():
    def __init__(self, position):
        self.x = position[0]
        self.y = position[1]

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
