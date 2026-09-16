import pygame
import os
import time
import math
import config
from core.globals import CHAR_DATA
from utils.sound_manager import play_sound


class Player(pygame.sprite.Sprite):
    def __init__(self, char_id, is_p2=False):
        super().__init__()
        self.char_data = CHAR_DATA.get(char_id, CHAR_DATA.get("choi", list(CHAR_DATA.values())[0]))
        self.char_id = str(char_id).lower()

        char_prefix = self.char_data["name"].lower()
        self.sprite_size = (130, 130)

        def load_img(suffix, fallback_color):
            path = f"assets/images/{char_prefix}_{suffix}.png"
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert()
                    img.set_colorkey((0, 0, 0))   # 검은 배경 투명 처리
                    img = pygame.transform.scale(img, self.sprite_size)
                    return img
                except Exception as e:
                    print(f"플레이어 이미지 로드 실패: {path} / {e}")

            surf = pygame.Surface(self.sprite_size, pygame.SRCALPHA)
            surf.fill(fallback_color)
            return surf

        color = config.CYAN if is_p2 else config.WHITE
        self.img_default = load_img("default", color)
        self.img_attack = load_img("attack", config.RED)
        self.img_skill = load_img("skill", config.YELLOW)

        self.image = self.img_default
        self.rect = self.image.get_rect()
        self.rect.center = (
            config.SCREEN_WIDTH // 2 + (30 if is_p2 else -30),
            config.SCREEN_HEIGHT // 2
        )

        self.is_p2 = is_p2
        self.base_speed = self.char_data["speed"]
        self.hp = self.char_data["hp"]
        self.max_hp = self.char_data["hp"]
        self.attack_radius = self.char_data["attack_radius"]
        self.attack_damage = self.char_data["attack_damage"]
        self.attack_cooldown = self.char_data["attack_cooldown"]
        self.skill_duration = self.char_data["skill_duration"]
        self.skill_cooldown = self.char_data["skill_cooldown"]
        self.attack_type = self.char_data.get("attack_type", "melee")
        self.skill_type = self.char_data.get("skill_type", "speed_boost")

        self.last_attack_time = time.time()
        self.skill_active = False
        self.skill_timer = 0
        self.last_skill_time = 0
        self.wants_to_use_skill = False
        self.wants_to_attack = False
        self.invincible = False
        self.last_direction = (1, 0)

        self.last_step_sound = 0
        self.step_interval = 0.25

    @property
    def hitbox(self):
        return self.rect.inflate(-120, -120)

    def update(self, time_delta):
        keys = pygame.key.get_pressed()
        speed = self.base_speed

        if self.skill_type == "buff_x2" and self.skill_active:
            speed = self.base_speed * 2

        dx, dy = 0, 0

        if not self.is_p2:
            if keys[pygame.K_a] and self.rect.left > 0:
                dx -= speed
            if keys[pygame.K_d] and self.rect.right < config.SCREEN_WIDTH:
                dx += speed
            if keys[pygame.K_w] and self.rect.top > 0:
                dy -= speed
            if keys[pygame.K_s] and self.rect.bottom < config.SCREEN_HEIGHT:
                dy += speed

            if keys[pygame.K_f] and time.time() - self.last_skill_time > self.skill_cooldown:
                self.wants_to_use_skill = True

            if keys[pygame.K_SPACE]:
                self.wants_to_attack = True
        else:
            if keys[pygame.K_LEFT] and self.rect.left > 0:
                dx -= speed
            if keys[pygame.K_RIGHT] and self.rect.right < config.SCREEN_WIDTH:
                dx += speed
            if keys[pygame.K_UP] and self.rect.top > 0:
                dy -= speed
            if keys[pygame.K_DOWN] and self.rect.bottom < config.SCREEN_HEIGHT:
                dy += speed

            if keys[pygame.K_RSHIFT] and time.time() - self.last_skill_time > self.skill_cooldown:
                self.wants_to_use_skill = True

        self.rect.x += dx
        self.rect.y += dy

        now = time.time()

        if dx != 0 or dy != 0:
            if now - self.last_step_sound > self.step_interval:
                play_sound("걷는 효과음.mp3", volume=0.35)
                self.last_step_sound = now

            mag = math.hypot(dx, dy)
            if mag != 0:
                self.last_direction = (dx / mag, dy / mag)

        if self.skill_active and time.time() > self.skill_timer:
            self.skill_active = False
            self.invincible = False

        if self.skill_active:
            self.image = self.img_skill
        elif time.time() - self.last_attack_time < 0.2:
            self.image = self.img_attack
        else:
            self.image = self.img_default

        if self.last_direction[0] > 0:
            self.image = pygame.transform.flip(self.image, True, False)

    def draw_hp(self, surface):
        if self.hp > 0:
            bar_w = 80
            bar_h = 8
            pct = self.hp / self.max_hp

            bar_x = self.rect.centerx - (bar_w // 2)
            bar_y = self.rect.bottom - 10

            pygame.draw.rect(surface, (180, 0, 0), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(surface, (255, 255, 0), (bar_x, bar_y, int(bar_w * pct), bar_h))