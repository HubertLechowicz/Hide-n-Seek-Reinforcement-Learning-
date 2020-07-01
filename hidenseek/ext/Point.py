class Point():
    def __init__(self, position):
        self.x = position[0]
        self.y = position[1]

    def __add__(self, obj):
        return Point((self.x + obj.x, self.y + obj.y))

    def __eq__(self, obj):
        return self.x == obj.x and self.y == obj.y

    def __str__(self):
        return "Point( " + str(self.x) + ' , ' + str(self.y) + ' )'