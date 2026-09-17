import pygame
import math
import config
import os

class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, target_pos, damage, speed=10, is_homerun=False):
        super().__init__()
        self.is_homerun = is_homerun
        
        # 1. 속성 결정
        size = 80 if is_homerun else 70
        
        # 2. 이미지 생성
        if not self.is_homerun:
            try:
                # 공유 투사체 이미지 로드
                img_path = os.path.join("assets", "images", "gongyu_attack_tool.png")
                raw_img = pygame.image.load(img_path).convert_alpha()
                self.image = pygame.transform.scale(raw_img, (size, size))
            except Exception:
                # 실패 시 기본 파란색 사각형
                self.image = pygame.Surface((size, size))
                self.image.fill((0, 0, 255))
        else:
            try:
                # 우식(홈런) 투사체 이미지 로드
                img_path = os.path.join("assets", "images", "woosik_attack_tool.png")
                raw_img = pygame.image.load(img_path).convert_alpha()
                self.image = pygame.transform.scale(raw_img, (size, size))
            except Exception:
                # 실패 시 기존 노란 원
                self.image = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(self.image, (255, 255, 0), (size//2, size//2), size//2)
            
        self.rect = self.image.get_rect(center=pos)
        
        # 3. 이동 로직
        self.pos_x = float(pos[0])
        self.pos_y = float(pos[1])
        self.damage = damage
        # 창 크기(UI_SCALE)에 따라 화면 자체의 실제 픽셀 크기가 달라지는데,
        # 투사체 속도는 그동안 고정 픽셀 값이라 큰 화면에서는 상대적으로
        # 느리게 느껴졌습니다. 다른 이동 관련 수치들과 마찬가지로 UI_SCALE을
        # 곱해서 화면 크기와 상관없이 체감 속도가 비슷하게 맞춥니다.
        self.speed = speed * config.UI_SCALE
        
        dx = target_pos[0] - pos[0]
        dy = target_pos[1] - pos[1]
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.dir_x = dx / dist
            self.dir_y = dy / dist
        else:
            self.dir_x = 1
            self.dir_y = 0
            
    def update(self, time_delta):
        self.pos_x += self.dir_x * self.speed
        self.pos_y += self.dir_y * self.speed
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)
        
        # 맵이 화면보다 넓어졌으므로, 화면 밖으로 나갔다고 바로 없애면 카메라
        # 바깥(아직 월드 안)에서 날아가는 투사체가 너무 일찍 사라집니다.
        # 월드 경계를 기준으로 판정합니다.
        if (self.rect.right < 0 or self.rect.left > config.WORLD_WIDTH
                or self.rect.bottom < 0 or self.rect.top > config.WORLD_HEIGHT):
            self.kill()
