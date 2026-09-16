# item.py

import pygame
import os
import random
import config

class Item(pygame.sprite.Sprite):
    def __init__(self, center):
        super().__init__()

        # item1.png, item2.png, item3.png 중 하나 랜덤 선택
        img_name = random.choice(["item1.png", "item2.png", "item3.png"])
        img_path = os.path.join("assets", "images", img_name)

        try:
            loaded_img = pygame.image.load(img_path).convert_alpha()
            self.image = pygame.transform.scale(loaded_img, (40, 40))
        except Exception as e:
            print(f"아이템 이미지 로드 실패: {e}")
            self.image = pygame.Surface((40, 40))
            self.image.fill(config.PURPLE)

        self.rect = self.image.get_rect(center=center)

    def update(self, *_):
        pass