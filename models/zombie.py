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

        # 창 크기(UI_SCALE)에 맞춰 다른 스프라이트들처럼 좀비 크기도 같이
        # 커지거나 작아지도록 기본 크기에 UI_SCALE을 곱합니다.
        base_w = round(s["size"][0] * config.UI_SCALE)
        base_h = round(s["size"][1] * config.UI_SCALE)

        # 보스(boss1/boss2)를 제외한 "잡졸" 좀비들은 크기에 무작위 변화를 줘서
        # 화면이 좀 더 다채롭게 보이도록 합니다. 단, 두 가지 규칙을 지킵니다:
        # 1) 지금까지의 고정 크기가 "가장 작은" 크기가 되도록 배율은 항상 1.0 이상만 적용
        # 2) 아무리 커져도 보스 좀비보다는 확실히 작아야 함(최대 배율 1.6배로 제한 —
        #    가장 큰 잡졸(mutant, 105px)이 168px까지 커져도 보스(250px)보다 훨씬 작음)
        if zombie_type in ("boss1", "boss2"):
            size_scale = 1.0
        else:
            size_scale = random.uniform(1.0, 1.6)

        size = (round(base_w * size_scale), round(base_h * size_scale))

        self.frames = get_zombie_frames(zombie_type, size)
        self.current_frame = 0
        self.anim_timer = 0.0
        self.anim_interval = 0.3
        self.facing_left = False

        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()

        spawn_margin = max(size) // 2 + 20

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

        # 이동 속도/사거리도 화면 위 실제 거리이므로 UI_SCALE을 곱해, 창 크기가
        # 커져도 플레이어와 마찬가지로 체감 속도가 비슷하게 유지되도록 합니다.
        self.speed = (s["speed"] + (0.04 * max(stage - 1, 0))) * config.UI_SCALE
        self.max_hp = s["hp"] * stage
        self.hp = self.max_hp
        self.damage = s["damage"]

        self.is_ranged = (zombie_type == "ranged")
        self.ranged_cooldown = 3.0
        self.last_ranged_attack = 0
        self.ranged_range = 250 * config.UI_SCALE

        self.is_boss = zombie_type in ["boss1", "boss2"]

        self.last_idle_sound = time.time()
        self.idle_sound_interval = random.uniform(3.0, 6.0)

        # 화면 밖에서 갑자기 "뿅" 하고 나타나지 않도록, 스폰 직후 잠깐 커지며 나타나는 연출
        self.spawn_timer = 0.0
        self.spawn_duration = 0.0 if self.is_boss else 0.25

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
                # 분노 프레임도 화면 크기에 맞춰 스케일된 보스 크기와 동일하게
                # 맞춰서, 분노 상태로 바뀔 때 크기가 갑자기 달라지지 않게 합니다.
                _rage_size = (round(250 * config.UI_SCALE), round(250 * config.UI_SCALE))
                if self.zombie_type == "boss1":
                    self.frames = get_zombie_frames("boss1_rage", _rage_size)
                    self.current_frame = 0
                elif self.zombie_type == "boss2":  # ✅ 추가
                    self.frames = get_zombie_frames("boss2_rage", _rage_size)
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
            img = pygame.transform.flip(img, True, False)

        if self.spawn_timer < self.spawn_duration:
            self.spawn_timer += time_delta
            progress = min(self.spawn_timer / self.spawn_duration, 1.0)
            scale = 0.3 + 0.7 * progress
            alpha = int(255 * progress)
            w, h = img.get_size()
            new_size = (max(1, round(w * scale)), max(1, round(h * scale)))
            old_center = self.rect.center
            img = pygame.transform.smoothscale(img, new_size).copy()
            img.set_alpha(alpha)
            self.image = img
            self.rect = self.image.get_rect(center=old_center)
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