# utils/camera.py
"""
화면(SCREEN)보다 넓은 월드(WORLD) 안에서, 플레이어를 따라다니며 그중 화면
크기만큼만 잘라서 보여주는 카메라입니다.

이 게임의 모든 스프라이트(플레이어/좀비/투사체/이펙트/장애물)는 "월드 좌표"를
그대로 self.rect에 담고 있습니다(기존 코드와 동일 - 좌표 체계를 바꾸지
않았습니다). 실제로 화면에 그릴 때만 카메라의 offset을 빼서 "화면 좌표"로
변환합니다. 즉 충돌 판정/스킬 사거리 등 게임 로직은 지금까지처럼 rect를 그대로
쓰면 되고, draw()에서만 camera.apply()를 거치면 됩니다.
"""

import config


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def update(self, target_rect):
        """target_rect(보통 플레이어 rect, 2인 모드면 둘의 중간 지점)를
        화면 중앙에 오도록 카메라 위치를 갱신하고, 월드 경계 밖으로 카메라가
        나가지 않도록 clamp합니다."""
        self.x = target_rect.centerx - config.SCREEN_WIDTH / 2
        self.y = target_rect.centery - config.SCREEN_HEIGHT / 2

        max_x = max(0, config.WORLD_WIDTH - config.SCREEN_WIDTH)
        max_y = max(0, config.WORLD_HEIGHT - config.SCREEN_HEIGHT)
        self.x = max(0, min(self.x, max_x))
        self.y = max(0, min(self.y, max_y))

    def apply(self, rect):
        """월드 좌표 rect를 화면 좌표 rect로 변환합니다(그리기 전용)."""
        return rect.move(-round(self.x), -round(self.y))

    def apply_pos(self, pos):
        return (pos[0] - self.x, pos[1] - self.y)

    def offset(self):
        return (round(self.x), round(self.y))

    def visible_world_rect(self, margin=0):
        """지금 카메라에 실제로 보이는 월드 좌표 사각형(여유 margin 포함).
        화면 밖(=카메라 시야 밖) 가장자리에서 좀비를 스폰시키는 등,
        '보이는 범위' 기준으로 뭔가를 배치할 때 사용합니다."""
        import pygame
        return pygame.Rect(
            round(self.x) - margin,
            round(self.y) - margin,
            config.SCREEN_WIDTH + margin * 2,
            config.SCREEN_HEIGHT + margin * 2,
        )
