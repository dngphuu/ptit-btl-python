from __future__ import annotations

import random
import pygame

class Debris:
    """Tumbling debris chunk representing a destroyed brick."""
    def __init__(self, x: float, y: float, sprite: pygame.Surface) -> None:
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-4, -2)
        self.gravity = 0.2
        self.sprite = sprite.copy()
        self.alpha = 255.0
        self.fade_rate = 255.0 / (0.6 * 60) # 0.6s at 60fps
        self.rotation = 0.0
        self.rot_speed = random.uniform(-5, 5)

    def update(self) -> None:
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.alpha = max(0.0, self.alpha - self.fade_rate)
        self.rotation += self.rot_speed

    def draw(self, surface: pygame.Surface) -> None:
        if self.alpha <= 0:
            return
        self.sprite.set_alpha(int(self.alpha))
        rotated = pygame.transform.rotate(self.sprite, self.rotation)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect)


class PixelParticle:
    """Small pixel particles emitted upon brick destruction."""
    def __init__(self, x: float, y: float, color: tuple[int, int, int]) -> None:
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-5, -1)
        self.gravity = 0.2
        self.color = color
        self.alpha = 255.0
        self.fade_rate = 255.0 / (0.6 * 60)
        
    def update(self) -> None:
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.alpha = max(0.0, self.alpha - self.fade_rate)

    def draw(self, surface: pygame.Surface) -> None:
        if self.alpha <= 0:
            return
        surf = pygame.Surface((2, 2), pygame.SRCALPHA)
        surf.fill((*self.color, int(self.alpha)))
        surface.blit(surf, (int(self.x), int(self.y)))


class DebrisManager:
    """Manages tumbling debris and pixel particles for destroyed bricks."""
    def __init__(self) -> None:
        self.debris: list[Debris] = []
        self.particles: list[PixelParticle] = []

    def spawn(self, x: float, y: float, sprite: pygame.Surface, color: tuple[int, int, int]) -> None:
        self.debris.append(Debris(x, y, sprite))
        for _ in range(random.randint(5, 10)):
            self.particles.append(PixelParticle(x, y, color))

    def update(self) -> None:
        for d in self.debris:
            d.update()
        for p in self.particles:
            p.update()
            
        self.debris = [d for d in self.debris if d.alpha > 0]
        self.particles = [p for p in self.particles if p.alpha > 0]

    def draw(self, surface: pygame.Surface) -> None:
        for p in self.particles:
            p.draw(surface)
        for d in self.debris:
            d.draw(surface)
