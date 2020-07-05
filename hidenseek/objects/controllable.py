import pygame
from ext.supportive import Point
import copy

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

        image_inplace = pygame.Surface((width, height))
        image_inplace.fill((0, 0, 0, 0))
        image_inplace.set_colorkey((0, 0, 0))

        pygame.draw.rect(
            image_inplace,
            color,
            (0, 0, width, height),
            0
        )

        self.sprite_index = 0
        image_movement = pygame.Surface((width, height))
        image_movement.fill((0, 0, 0, 0))
        image_movement.set_colorkey((0, 0, 0))

        pygame.draw.rect(
            image_movement,
            (64, 128, 240),
            (0, 0, width, height),
            0
        )

        self.images = [image_inplace] + [image_movement for _ in range(10)]
        self.image = image_inplace
        self.rect = self.image.get_rect()
        self.rect.center = (self.pos_init.x, self.pos_init.y)

    def update(self, movement, dt):
        old_pos = copy.deepcopy(self.pos)
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

        if old_pos != self.pos:
            self.sprite_index = (self.sprite_index + 1) % len(self.images)
            self.image = self.images[self.sprite_index]
