# effects.py

import pygame

class AttackEffect(pygame.sprite.Sprite):
    def __init__(self, center, radius):
        super().__init__()

        try:
            raw = pygame.image.load("assets/images/effect1.png").convert_alpha()
            size = radius * 2
            self.image = pygame.transform.scale(raw, (size, size))
        except Exception:
            self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)

        self.rect = self.image.get_rect(center=center)

        self.timer = 0
        self.lifetime = 0.15

    def update(self, time_delta):
        self.timer += time_delta
        if self.timer >= self.lifetime:
            self.kill()

class HitEffect(pygame.sprite.Sprite):
    def __init__(self, center_pos):
        super().__init__()

        try:
            raw = pygame.image.load("assets/images/effect2.png").convert_alpha()
            self.image = pygame.transform.scale(raw, (40, 40))
        except Exception:
            self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
            self.image.fill((255, 0, 0, 180))

        self.rect = self.image.get_rect(center=center_pos)

        self.timer = 0
        self.lifetime = 0.15

    def update(self, time_delta):
        self.timer += time_delta
        if self.timer >= self.lifetime:
            self.kill()