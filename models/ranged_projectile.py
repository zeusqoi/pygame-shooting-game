import pygame
import math
import config

class RangedProjectile(pygame.sprite.Sprite):
    """원거리 좀비가 플레이어에게 발사하는 투사체"""
    def __init__(self, pos, target_pos, damage=1, speed=5):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill((255, 50, 50))
        self.rect = self.image.get_rect(center=pos)
        self.pos_x = float(pos[0])
        self.pos_y = float(pos[1])
        self.damage = damage
        # 다른 이동 속도 값들과 마찬가지로 UI_SCALE만큼 곱해서, 창 크기가
        # 커져도 체감 속도가 비슷하게 유지되도록 합니다.
        self.speed = speed * config.UI_SCALE

        dx = target_pos[0] - pos[0]
        dy = target_pos[1] - pos[1]
        dist = math.hypot(dx, dy)
        self.dir_x = dx / dist if dist > 0 else 0
        self.dir_y = dy / dist if dist > 0 else 1

    def update(self, time_delta):
        self.pos_x += self.dir_x * self.speed
        self.pos_y += self.dir_y * self.speed
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

        if (self.rect.right < 0 or self.rect.left > config.SCREEN_WIDTH or
                self.rect.bottom < 0 or self.rect.top > config.SCREEN_HEIGHT):
            self.kill()