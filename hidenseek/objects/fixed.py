import math

import pygame
import copy
from ext.supportive import Point


class Wall(pygame.sprite.Sprite):
    """
    Wall Class for Hide'n'Seek Game, inherits from pygame.sprite.Sprite

    Attributes
    ----------
        owner : None, hidenseek.objects.controllable.Hiding, hidenseek.objects.controllable.Seeker
            Wall owner, None for game environment
        width : int
            width of the Wall
        height : int
            height of the Wall
        pos : hidenseek.ext.supportive.Point
            object position on the game display
        image : pygame.Surface
            object image surface on which image/shape will be drawn
        rect : pygame.Rect
            object Rectangle, to be drawn
        polygon_points : list of tuples
            vertices, used for collision check in SAT

    Methods
    -------
        is_outside_map():
            checks whenever Wall is outside map (game screen)
        get_abs_vertices():
            returns absolute vertices coordinates (in game screen coordinates system)
    """

    def __init__(self, owner, cfg, x, y):
        """
        Constructs all neccesary attributes for the Wall Object

        Parameters
        ----------
            owner : None, hidenseek.objects.controllable.Hiding, hidenseek.objects.controllable.Seeker
                Wall owner, None for game environment
            cfg : configparser Object
                Wall Config
            x : float
                center of the rectangle in 'x' axis for absolute coordinate system (game screen)
            y : float
                center of the rectangle in 'y' axis for absolute coordinate system (game screen)
        """

        super().__init__()

        self.owner = owner

        self.width = cfg.getint('WIDTH', fallback=15)
        self.height = cfg.getint('HEIGHT', fallback=15)

        self.pos = Point((x, y))

        image = pygame.Surface((self.width, self.height))
        image.fill((0, 0, 0, 0))
        image.set_colorkey((0, 0, 0))

        pygame.draw.rect(
            image,
            (0, 255, 0), # green
            (0, 0, self.width, self.height),
            0
        )

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = (self.pos.x, self.pos.y)
        self.polygon_points = [Point((self.rect.left, self.rect.top)), Point((self.rect.right, self.rect.top)), Point((self.rect.right, self.rect.bottom)), Point((self.rect.left, self.rect.bottom))]

    def is_outside_map(self, SCREEN_WIDTH, SCREEN_HEIGHT):
        """
        Checks whenever Wall is outside map (game screen)

        Parameters
        ----------
            SCREEN_WIDTH : int
                width of the game window
            SCREEN_HEIGHT : int
                height of the game window
        
        Returns
        -------
            is_outside_map : bool
        """

        if self.pos.y - self.height / 2 <= 0 or self.pos.y + self.height / 2 >= SCREEN_HEIGHT or self.pos.x - self.width / 2 <= 0 or self.pos.x + self.width / 2 >= SCREEN_WIDTH:
            return True
        return False
        
    def get_abs_vertices(self):
        """
        Returns absolute coordinates of Vertices in Polygon

        Parameters
        ----------
            None
        
        Returns
        -------
            points : list of hidenseek.ext.supportive.Point
                self.pylogon_points mapped to the absolute coordinates system
        """

        return self.polygon_points

    def rotate(self, angle, position):
        """
        Rotates the sprite by creating new Rectangle and updates its polygon points

        Parameters
        ----------
            angle : float
                player direction in radians
            position : Point
                center of the wall

        Returns
        -------
            None
        """
        # Copy and then rotate the original image.
        copied_image = self.image.copy()
        self.image = pygame.transform.rotozoom(copied_image, -angle*180/math.pi, 1)
        self.image.set_colorkey((0, 0, 0))
        
        # Create a new rect with the center of the sprite.
        self.rect = self.image.get_rect()
        self.rect.center = (position.x,position.y)
        self.width = self.rect.width
        self.height = self.rect.height

        # Update the polygon points for collisions
        self.polygon_points = [Point.triangle_unit_circle_relative(angle, self.pos, polygon_point) for polygon_point in self.polygon_points]