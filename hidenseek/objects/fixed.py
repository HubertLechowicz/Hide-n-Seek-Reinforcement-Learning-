import pygame
from ext.supportive import Point

class Wall(pygame.sprite.Sprite):
    def __init__(self, width, height, x, y):
        super().__init__()
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
