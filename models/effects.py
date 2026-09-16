# effects.py

import pygame


class AttackEffect(pygame.sprite.Sprite):
    """범위 공격 이펙트. 작게 시작해서 커지며 서서히 사라지는 '충격파' 애니메이션."""

    def __init__(self, center, radius):
        super().__init__()

        try:
            self._raw = pygame.image.load("assets/images/effect1.png").convert_alpha()
        except Exception:
            self._raw = None

        self.center = center
        self.target_size = max(1, radius * 2)

        self.timer = 0
        self.lifetime = 0.25  # 기존 0.15초는 너무 짧아 눈에 잘 보이지 않았습니다.

        self.image = self._render_frame(0.0)
        self.rect = self.image.get_rect(center=center)

    def _render_frame(self, progress):
        # progress: 0(발동 직후) ~ 1(소멸 직전)
        scale = 0.55 + 0.45 * min(progress * 2.2, 1.0)  # 작게 시작해서 빠르게 확대
        size = max(1, int(self.target_size * scale))
        alpha = max(0, int(255 * (1.0 - progress) ** 1.5))

        if self._raw is not None:
            surf = pygame.transform.smoothscale(self._raw, (size, size)).copy()
            surf.set_alpha(alpha)
        else:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
        return surf

    def update(self, time_delta):
        self.timer += time_delta
        if self.timer >= self.lifetime:
            self.kill()
            return

        progress = self.timer / self.lifetime
        old_center = self.rect.center
        self.image = self._render_frame(progress)
        self.rect = self.image.get_rect(center=old_center)


class HitEffect(pygame.sprite.Sprite):
    """피격 이펙트. 살짝 튀어오르듯 커졌다가(팝) 서서히 사라집니다."""

    def __init__(self, center_pos):
        super().__init__()

        try:
            self._raw = pygame.image.load("assets/images/effect2.png").convert_alpha()
        except Exception:
            self._raw = None

        self.center = center_pos
        self.base_size = 40

        self.timer = 0
        self.lifetime = 0.25

        self.image = self._render_frame(0.0)
        self.rect = self.image.get_rect(center=center_pos)

    def _render_frame(self, progress):
        if progress < 0.4:
            scale = 1.0 + 0.5 * (progress / 0.4)
        else:
            scale = 1.5 - 0.3 * ((progress - 0.4) / 0.6)
        size = max(1, int(self.base_size * scale))
        alpha = max(0, int(255 * (1.0 - progress)))

        if self._raw is not None:
            surf = pygame.transform.smoothscale(self._raw, (size, size)).copy()
            surf.set_alpha(alpha)
        else:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            surf.fill((255, 0, 0, alpha))
        return surf

    def update(self, time_delta):
        self.timer += time_delta
        if self.timer >= self.lifetime:
            self.kill()
            return

        progress = self.timer / self.lifetime
        old_center = self.rect.center
        self.image = self._render_frame(progress)
        self.rect = self.image.get_rect(center=old_center)
