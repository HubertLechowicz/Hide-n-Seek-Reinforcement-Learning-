import pygame
from ext.supportive import Point

class Player(pygame.sprite.Sprite):
    def __init__(self, width, height, speed, pos_ratio, color, SCREEN_WIDTH, SCREEN_HEIGHT):
        super().__init__()
        self.width = width
        self.height = height

        self.pos_init = Point((pos_ratio[0] * SCREEN_WIDTH, pos_ratio[1] * SCREEN_HEIGHT))
        self.pos = Point((pos_ratio[0] * SCREEN_WIDTH, pos_ratio[1] * SCREEN_HEIGHT))

        self.SCREEN_WIDTH = SCREEN_WIDTH
        self.SCREEN_HEIGHT = SCREEN_HEIGHT

        self.velocity = speed # how fast it should move

        image = pygame.Surface((width, height))
        image.fill((0, 0, 0, 0))
        image.set_colorkey((0, 0, 0))

        pygame.draw.rect(
            image,
            color,
            (0, 0, width, height),
            0
        )

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = (self.pos_init.x, self.pos_init.y)

    def update(self, movement, dt):
        self.pos += self.velocity * Point((movement.x * dt, movement.y * dt))

        if self.pos.y - self.height / 2 <= 0:
            self.pos.y = self.height / 2

        if self.pos.y + self.height / 2 >= self.SCREEN_HEIGHT:
            self.pos.y = self.SCREEN_HEIGHT - self.height / 2

        if self.pos.x - self.width / 2 <= 0:
            self.pos.x = self.width / 2

        if self.pos.x + self.width / 2 >= self.SCREEN_WIDTH:
            self.pos.x = self.SCREEN_WIDTH - self.width / 2

        self.rect.center = (self.pos.x, self.pos.y)