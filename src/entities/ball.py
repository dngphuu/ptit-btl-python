"""
src/entities/ball.py
====================
Ball entity.
"""

from __future__ import annotations

import math
import pygame

from src.entities.playfield import Playfield
from src.entities.paddle import Paddle
from src.entities.brick_grid import BrickGrid

class Ball:
    def __init__(self, playfield: Playfield, paddle: Paddle) -> None:
        self.playfield = playfield
        self.paddle = paddle
        self.radius = 8
        self.base_speed = 180.0
        self.current_speed = self.base_speed
        self.acceleration = 1.0  # Base acceleration over time
        self.score_multiplier = 1.0
        self.active = False
        
        try:
            img = pygame.image.load("assets/game_element.png").convert_alpha()
            sprite = img.subsurface(pygame.Rect(971, 125, 65, 65))
            self.image = pygame.transform.smoothscale(sprite, (self.radius * 2, self.radius * 2))
        except Exception:
            self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (200, 200, 200), (self.radius, self.radius), self.radius)
            
        self.reset()
        
    def set_difficulty(self, level: int) -> None:
        """Applies a difficulty curve for speed, acceleration, and score multiplier."""
        curve_factor = (level - 1) ** 1.2
        self.base_speed = 180.0 + curve_factor * 15.0
        self.acceleration = 0.5 + curve_factor * 0.3
        self.score_multiplier = 1.0 + curve_factor * 0.3
        
    def reset(self) -> None:
        self.active = False
        self.x = self.paddle.x
        self.y = self.paddle.rect.top - self.radius - 1
        self.current_speed = self.base_speed
        self.vx = self.current_speed * 0.707
        self.vy = -self.current_speed * 0.707

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            round(self.x - self.radius),
            round(self.y - self.radius),
            self.radius * 2,
            self.radius * 2
        )

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper, brick_grid: BrickGrid) -> int:
        points_earned = 0
        if not self.active:
            self.x = self.paddle.x
            self.y = self.paddle.rect.top - self.radius - 1
            if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
                self.active = True
                self.current_speed = self.base_speed
                length = math.hypot(self.vx, self.vy)
                if length != 0:
                    self.vx = (self.vx / length) * self.current_speed
                    self.vy = (self.vy / length) * self.current_speed
            return points_earned
            
        # Acceleration over time
        self.current_speed = min(1200.0, self.current_speed + self.acceleration * dt)
        
        # Normalize and apply speed
        length = math.hypot(self.vx, self.vy)
        if length != 0:
            self.vx = (self.vx / length) * self.current_speed
            self.vy = (self.vy / length) * self.current_speed
            
        # Move
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        bounced = False
        
        # Slanted wall collisions
        left_edge = self.playfield.get_left_edge(self.y)
        right_edge = self.playfield.get_right_edge(self.y)
        
        if self.x - self.radius < left_edge:
            self.x = left_edge + self.radius
            if self.vx < 0:
                self.vx *= -1
                bounced = True
        elif self.x + self.radius > right_edge:
            self.x = right_edge - self.radius
            if self.vx > 0:
                self.vx *= -1
                bounced = True
            
        if self.y - self.radius < self.playfield.top:
            self.y = self.playfield.top + self.radius
            if self.vy < 0:
                self.vy *= -1
                bounced = True
            
        # Paddle collision
        if self.vy > 0 and self.rect.colliderect(self.paddle.rect):
            self.y = self.paddle.rect.top - self.radius
            bounced = True
            
            # Bounce angle
            hit_pos = (self.x - self.paddle.rect.left) / self.paddle.width
            hit_pos = max(0.0, min(1.0, hit_pos))
            angle = (hit_pos - 0.5) * math.pi / 2.5
            
            # Base reflection
            self.vx = self.current_speed * math.sin(angle)
            self.vy = -self.current_speed * math.cos(angle)
            
            # Impart paddle velocity (English)
            self.vx += self.paddle.vx * 0.35
            
            # Ensure it always bounces upward
            if self.vy > -50:
                self.vy = -50
                
            # Re-normalize vector after english
            new_length = math.hypot(self.vx, self.vy)
            if new_length != 0:
                self.vx = (self.vx / new_length) * self.current_speed
                self.vy = (self.vy / new_length) * self.current_speed
            
        # Brick collision
        for brick in brick_grid.alive_bricks():
            if self.rect.colliderect(brick.rect):
                bounced = True
                destroyed = brick.hit()
                if destroyed:
                    points_earned += int(50 * self.score_multiplier)
                else:
                    points_earned += int(10 * self.score_multiplier)
                    
                overlap_left = (self.x + self.radius) - brick.rect.left
                overlap_right = brick.rect.right - (self.x - self.radius)
                overlap_top = (self.y + self.radius) - brick.rect.top
                overlap_bottom = brick.rect.bottom - (self.y - self.radius)
                
                min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
                if min_overlap == overlap_top or min_overlap == overlap_bottom:
                    self.vy *= -1
                else:
                    self.vx *= -1
                break

        if bounced:
            self.current_speed = min(1200.0, self.current_speed + 1.0)

        # Fall out of bounds
        if self.y > self.playfield.bottom:
            self.reset()
            # Lives should be decremented externally

        return points_earned

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, (round(self.x - self.radius), round(self.y - self.radius)))
