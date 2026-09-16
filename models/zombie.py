import pygame
import random
import math
import time
import os
import config
from utils.sound_manager import play_sound

_zombie_frames_cache = {}


def get_zombie_frames(z_type, size):
    cache_key = (z_type, size)
    if cache_key in _zombie_frames_cache:
        return _zombie_frames_cache[cache_key]

    frames = []

    img_map = {
    "soldier": ["z1-1.png", "z1-2.png", "z1-3.png"],
    "explode": ["z2-1.png", "z2-2.png", "z2-3.png", "z2-4.png"],
    "mutant": ["z3-1.png", "z3-2.png", "z3-3.png"],
    "ranged": ["z4-1.png", "z4-2.png"],
    "boss1": ["boss1-1.png", "boss1-2.png", "boss1-3.png", "boss1-4.png"],
    "boss1_rage": ["boss1-5.png", "boss1-6.png"],  # ✅ 기존
    "boss2": ["boss2-1.png", "boss2-2.png", "boss2-3.png"],
    "boss2_rage": ["boss2-4.png", "boss2-5.png"],  # ✅ 추가
}

    file_names = img_map.get(z_type, img_map["soldier"])

    for fn in file_names:
        path = os.path.join("assets", "images", fn)
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert()
                img.set_colorkey((0, 0, 0))   # 검은 배경 투명 처리
                img = pygame.transform.scale(img, size)
                frames.append(img)
            except Exception as e:
                print(f"좀비 이미지 로드 실패: {fn} / {e}")

    if not frames:
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((255, 0, 255))
        frames.append(surf)

    _zombie_frames_cache[cache_key] = frames
    return frames


class Zombie(pygame.sprite.Sprite):
    def __init__(self, stage, targets, zombie_type="soldier"):
        super().__init__()
        self.zombie_type = zombie_type
        self.targets = targets
        self.is_enraged = False  # ✅ 분노 상태
        self.enrage_threshold = 0.3  # ✅ HP 30% 이하면 분노

        stats = {
            "soldier": {"color": (0, 100, 0),   "hp": 10,  "speed": 0.55, "damage": 1, "size": (90, 90)},
            "explode": {"color": (200, 100, 0), "hp": 8,   "speed": 0.75, "damage": 3, "size": (88, 88)},
            "mutant":  {"color": (100, 0, 150), "hp": 20,  "speed": 0.42, "damage": 2, "size": (105, 105)},
            "ranged":  {"color": (0, 50, 150),  "hp": 6,   "speed": 0.48, "damage": 1, "size": (88, 88)},
            "boss1":   {"color": (180, 0, 0),   "hp": 200, "speed": 0.35, "damage": 5, "size": (250, 250)},
            "boss2":   {"color": (80, 0, 80),   "hp": 350, "speed": 0.45, "damage": 8, "size": (250, 250)},
        }
        s = stats.get(zombie_type, stats["soldier"])

        self.frames = get_zombie_frames(zombie_type, s["size"])
        self.current_frame = 0
        self.anim_timer = 0.0
        self.anim_interval = 0.3
        self.facing_left = False

        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()

        spawn_margin = max(s["size"]) // 2 + 20

        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            self.rect.center = (random.randint(0, config.SCREEN_WIDTH), -spawn_margin)
        elif side == "bottom":
            self.rect.center = (random.randint(0, config.SCREEN_WIDTH), config.SCREEN_HEIGHT + spawn_margin)
        elif side == "left":
            self.rect.center = (-spawn_margin, random.randint(0, config.SCREEN_HEIGHT))
        else:
            self.rect.center = (config.SCREEN_WIDTH + spawn_margin, random.randint(0, config.SCREEN_HEIGHT))

        self.pos_x = float(self.rect.x)
        self.pos_y = float(self.rect.y)

        self.speed = s["speed"] + (0.04 * max(stage - 1, 0))
        self.max_hp = s["hp"] * stage
        self.hp = self.max_hp
        self.damage = s["damage"]

        self.is_ranged = (zombie_type == "ranged")
        self.ranged_cooldown = 3.0
        self.last_ranged_attack = 0
        self.ranged_range = 250

        self.is_boss = zombie_type in ["boss1", "boss2"]

        self.last_idle_sound = time.time()
        self.idle_sound_interval = random.uniform(3.0, 6.0)

    @property
    def hitbox(self):
        # 플레이어에게 맞을 때의 판정 (때리기 쉽게 크기를 키움)
        return self.rect.inflate(-10, -10)

    @property
    def damage_hitbox(self):
        # 플레이어를 때릴 때의 판정 (플레이어가 부당하게 맞지 않도록 기존의 좁은 크기 유지)
        return self.rect.inflate(-40, -40)

    def update(self, time_delta):
        if self.is_boss and not self.is_enraged:
            if self.hp / self.max_hp <= 0.3:
                self.is_enraged = True
                self.speed *= 1.5
                self.anim_interval = 0.15
                if self.zombie_type == "boss1":
                    self.frames = get_zombie_frames("boss1_rage", (250, 250))
                    self.current_frame = 0
                elif self.zombie_type == "boss2":  # ✅ 추가
                    self.frames = get_zombie_frames("boss2_rage", (250, 250))
                    self.current_frame = 0

        closest_p = None
        min_dist = float("inf")

        for p in self.targets:
            if p.hp > 0:
                dist = math.hypot(
                    p.rect.centerx - self.rect.centerx,
                    p.rect.centery - self.rect.centery
                )
                if dist < min_dist:
                    min_dist = dist
                    closest_p = p

        if closest_p:
            if min_dist < 250:
                now = time.time()
                if now - self.last_idle_sound > self.idle_sound_interval:
                    play_sound(
                        random.choice([
                            "좀비 기본 효과음1.mp3",
                            "좀비 기본 효과음 2.mp3"
                        ]),
                        volume=0.3
                    )
                    self.last_idle_sound = now
                    self.idle_sound_interval = random.uniform(3.0, 6.0)

            dx = closest_p.rect.centerx - self.rect.centerx
            dy = closest_p.rect.centery - self.rect.centery
            dist = math.hypot(dx, dy)

            if self.is_ranged and dist < self.ranged_range:
                pass
            elif dist > 0:
                move_step = self.speed * time_delta * 60
                self.pos_x += (dx / dist) * move_step
                self.pos_y += (dy / dist) * move_step
                self.rect.x = int(self.pos_x)
                self.rect.y = int(self.pos_y)

                if dx < 0:
                    self.facing_left = True
                elif dx > 0:
                    self.facing_left = False

        self.anim_timer += time_delta
        if self.anim_timer >= self.anim_interval:
            self.anim_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)

        img = self.frames[self.current_frame]
        if self.facing_left:
            self.image = pygame.transform.flip(img, True, False)
        else:
            self.image = img

    def draw_hp(self, surface):
        if self.hp > 0:
            bar_w = self.rect.width
            bar_h = 6 if self.is_boss else 4
            pct = self.hp / self.max_hp

            pygame.draw.rect(
                surface,
                (180, 0, 0),
                (self.rect.x, self.rect.y - 12, bar_w, bar_h)
            )
            pygame.draw.rect(
                surface,
                (0, 230, 0),
                (self.rect.x, self.rect.y - 12, int(bar_w * pct), bar_h)
            )