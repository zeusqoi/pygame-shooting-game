# item.py

import pygame
import os
import random
import config

# 아이템 종류별 정의: 이미지 파일 / 종류 키 / 이미지가 없을 때 대체로 그릴 색상.
# 각 종류는 game_scene.py에서 플레이어가 먹었을 때 서로 다른 효과를 줍니다.
# - heal : 즉시 체력 회복
# - speed: 일정 시간 이동속도 증가
# - shield: 일정 시간 무적
ITEM_DEFS = [
    {"key": "heal", "file": "item1.png", "color": config.GREEN},
    {"key": "speed", "file": "item2.png", "color": config.CYAN},
    {"key": "shield", "file": "item3.png", "color": config.YELLOW},
]


class Item(pygame.sprite.Sprite):
    def __init__(self, center, item_type=None):
        super().__init__()

        # item_type을 지정하지 않으면 세 종류 중 하나를 무작위로 고릅니다.
        item_def = next((d for d in ITEM_DEFS if d["key"] == item_type), None)
        if item_def is None:
            item_def = random.choice(ITEM_DEFS)

        self.item_type = item_def["key"]

        img_path = os.path.join("assets", "images", item_def["file"])

        try:
            loaded_img = pygame.image.load(img_path).convert_alpha()
            self.image = pygame.transform.scale(loaded_img, (40, 40))
        except Exception as e:
            print(f"아이템 이미지 로드 실패: {e}")
            # 이미지가 없을 때도 종류를 구분할 수 있도록, 종류별 색상의
            # 원으로 대체 표시합니다(기존에는 전부 같은 보라색 사각형이었음).
            self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(self.image, item_def["color"], (20, 20), 20)
            pygame.draw.circle(self.image, config.WHITE, (20, 20), 20, 2)

        self.rect = self.image.get_rect(center=center)

    def update(self, *_):
        pass
