class Point():
    def __init__(self, position):
        self.x = position[0]
        self.y = position[1]

    def __add__(self, obj):
        return Point((self.x + obj.x, self.y + obj.y))

    def __sub__(self, obj):
        return Point((self.x - obj.x, self.y - obj.y))

    def __eq__(self, obj):
        return self.x == obj.x and self.y == obj.y

    def __mul__(self, obj):
        if not (isinstance(obj, int) or isinstance(obj, float)):
            raise ValueError("You can only multiply Point by using Integer or Float")
        return Point((self.x * obj, self.y * obj))

    def __rmul__(self, obj):
        return self.__mul__(obj)

    def __str__(self):
        return "Point( " + str(self.x) + ' , ' + str(self.y) + ' )'
