import pygame
from ext.supportive import Point

class Wall(pygame.sprite.Sprite):
    def __init__(self, owner, width, height, x, y):
        super().__init__()

        self.owner = owner

        self.width = width
        self.height = height

        self.pos = Point((x, y))


        image = pygame.Surface((width, height))
        image.fill((0, 0, 0, 0))
        image.set_colorkey((0, 0, 0))

        pygame.draw.rect(
            image,
            (0, 255, 0), # green
            (0, 0, width, height),
            0
        )

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = (self.pos.x, self.pos.y)
        self.polygon_points = [(self.rect.left, self.rect.top), (self.rect.right, self.rect.top), (self.rect.right, self.rect.bottom), (self.rect.left, self.rect.bottom)]

    def is_outside_map(self, SCREEN_WIDTH, SCREEN_HEIGHT):
        if self.pos.y - self.height / 2 <= 0 or self.pos.y + self.height / 2 >= SCREEN_HEIGHT or self.pos.x - self.width / 2 <= 0 or self.pos.x + self.width / 2 >= SCREEN_WIDTH:
            return True
        return False
        
    def get_abs_vertices(self):
        """ Returns absolute coordinates of Vertices in Polygon """
        return [Point((x, y)) for x, y in self.polygon_points]