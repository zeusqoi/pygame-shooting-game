# models/obstacle.py

import pygame
import config


class Obstacle(pygame.sprite.Sprite):
    """맵에 놓이는 정적 장애물(잔해 더미, 컨테이너 등). 플레이어와 좀비 모두
    이 장애물은 통과하지 못하고 옆으로 미끄러지듯 피해서 지나갑니다(좀비는
    플로우필드 경로탐색으로, 플레이어는 축별 충돌 처리로)."""

    _PALETTE = [
        (70, 66, 60),
        (60, 58, 66),
        (66, 60, 60),
        (58, 64, 58),
    ]

    def __init__(self, world_x, world_y, width, height, color=None):
        super().__init__()
        color = color or Obstacle._PALETTE[(world_x + world_y) % len(Obstacle._PALETTE)]

        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        border = max(1, round(3 * config.UI_SCALE))
        pygame.draw.rect(self.image, (20, 20, 20), self.image.get_rect(), border)
        # 위쪽 가장자리를 살짝 밝게 해서 입체감을 줍니다.
        highlight = pygame.Rect(0, 0, width, max(2, height // 6))
        highlight_color = tuple(min(255, c + 25) for c in color)
        pygame.draw.rect(self.image, highlight_color, highlight)

        self.rect = self.image.get_rect(topleft=(round(world_x), round(world_y)))

    @property
    def hitbox(self):
        return self.rect
