"""
src/entities/paddle.py
======================
Paddle entity.
"""

from __future__ import annotations

import pygame

from src.config import PADDLE_SPEED, PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_Y_OFFSET
from src.entities.playfield import Playfield

class Paddle:
    def __init__(self, playfield: Playfield) -> None:
        self.playfield = playfield
        self.width = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT
        self.speed = PADDLE_SPEED
        self.x = playfield.center_x
        self.y = playfield.bottom - PADDLE_Y_OFFSET
        self.vx = 0.0
        
        try:
            img = pygame.image.load("assets/game_element.png").convert_alpha()
            sprite = img.subsurface(pygame.Rect(840, 135, 109, 53))
            self.image = pygame.transform.smoothscale(sprite, (self.width, 30))
        except Exception:
            self.image = pygame.Surface((self.width, 30), pygame.SRCALPHA)
            self.image.fill((100, 100, 100))

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            round(self.x - self.width / 2.0),
            round(self.y - self.height / 2.0),
            self.width,
            self.height
        )

    def update(self, keys: pygame.key.ScancodeWrapper, dt: float) -> None:
        prev_x = self.x
        
        # Use simple keyboard controls for now
        if keys[pygame.K_LEFT]:
            self.x -= self.speed * dt * 60
        if keys[pygame.K_RIGHT]:
            self.x += self.speed * dt * 60
            
        # Clamp to playfield boundaries (slanted walls)
        half_w = self.width / 2.0
        min_x = self.playfield.get_left_edge(self.y) + half_w
        max_x = self.playfield.get_right_edge(self.y) - half_w
        if self.x < min_x:
            self.x = min_x
        elif self.x > max_x:
            self.x = max_x
            
        if dt > 0:
            self.vx = (self.x - prev_x) / dt
        else:
            self.vx = 0.0

    def draw(self, surface: pygame.Surface) -> None:
        img_rect = self.image.get_rect(center=(round(self.x), round(self.y)))
        surface.blit(self.image, img_rect)
