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
    "boss1_rage": ["boss1-5.png", "boss1-6.png"],
    "boss2": ["boss2-1.png", "boss2-2.png", "boss2-3.png"],
    "boss2_rage": ["boss2-4.png", "boss2-5.png"],
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
    def __init__(self, stage, targets, zombie_type="soldier", obstacles=None, flow_field=None, spawn_rect=None):
        super().__init__()
        self.zombie_type = zombie_type
        self.targets = targets
        self.is_enraged = False  # 분노 상태
        self.enrage_threshold = 0.3  # HP 30% 이하면 분노

        # 장애물을 피해서 이동하기 위한 참조들. obstacles는 직접 충돌(밀어내기)
        # 판정용, flow_field는 "지금 이 칸에서 어느 방향이 플레이어로 가는
        # 가장 가까운 길인지"를 조회하는 경로탐색용입니다. 둘 다 None이면
        # (예: 기존 테스트 코드) 예전처럼 플레이어를 향해 직선으로만 움직입니다.
        self.obstacles = obstacles
        self.flow_field = flow_field

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

        # spawn_rect: 카메라에 지금 보이는 월드 영역(Camera.visible_world_rect()).
        # 기존처럼 "화면 가장자리 바로 밖"에서 나타나는 느낌을 유지하되, 좌표
        # 기준은 화면이 아니라 카메라가 보고 있는 월드 영역이 됩니다. spawn_rect가
        # 없으면(예: 기존 테스트 코드) 월드 전체를 화면으로 간주하고 예전과 동일하게 동작합니다.
        view = spawn_rect if spawn_rect is not None else pygame.Rect(0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT)

        side = random.choice(["top", "bottom", "left", "right"])
        if side == "top":
            self.rect.center = (random.randint(view.left, view.right), view.top - spawn_margin)
        elif side == "bottom":
            self.rect.center = (random.randint(view.left, view.right), view.bottom + spawn_margin)
        elif side == "left":
            self.rect.center = (view.left - spawn_margin, random.randint(view.top, view.bottom))
        else:
            self.rect.center = (view.right + spawn_margin, random.randint(view.top, view.bottom))

        # 월드 밖으로 스폰되지 않도록 안전하게 한 번 더 범위를 고정합니다.
        self.rect.centerx = max(0, min(config.WORLD_WIDTH, self.rect.centerx))
        self.rect.centery = max(0, min(config.WORLD_HEIGHT, self.rect.centery))

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

    def _try_move_axis(self, step_dx, step_dy):
        """장애물과 겹치면 그 축의 이동만 취소합니다(플레이어 쪽과 동일한
        방식). 플로우 필드가 대부분의 경로를 알아서 피해가지만, 격자 칸
        하나 안에서 장애물 모서리에 살짝 스치는 정도는 이걸로 막아줍니다."""
        if not self.obstacles:
            self.pos_x += step_dx
            self.pos_y += step_dy
            self.rect.x = int(self.pos_x)
            self.rect.y = int(self.pos_y)
            return

        if step_dx != 0:
            new_x = self.pos_x + step_dx
            test_rect = self.rect.copy()
            test_rect.x = int(new_x)
            if not any(test_rect.colliderect(o.hitbox) for o in self.obstacles):
                self.pos_x = new_x
                self.rect.x = int(self.pos_x)

        if step_dy != 0:
            new_y = self.pos_y + step_dy
            test_rect = self.rect.copy()
            test_rect.y = int(new_y)
            if not any(test_rect.colliderect(o.hitbox) for o in self.obstacles):
                self.pos_y = new_y
                self.rect.y = int(self.pos_y)

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
                elif self.zombie_type == "boss2":
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
                # 장애물이 있는 맵에서는 플레이어를 향한 직선 벡터 대신, 미리
                # 계산해둔 플로우 필드에서 "지금 칸에서 플레이어로 가는 가장
                # 가까운 길" 방향을 조회해서 그쪽으로 움직입니다(장애물을 자연스럽게
                # 돌아감). 플로우 필드가 없거나 이 칸에 대한 경로 정보가 없으면
                # (막힌 구역에 갇혔거나 아직 계산 전이면) 기존처럼 직선으로 이동합니다.
                move_dir = None
                if self.flow_field is not None:
                    move_dir = self.flow_field.get_direction(self.rect.center)

                if move_dir is None:
                    move_dir = (dx / dist, dy / dist)

                move_step = self.speed * time_delta * 60
                step_dx = move_dir[0] * move_step
                step_dy = move_dir[1] * move_step
                self._try_move_axis(step_dx, step_dy)

                if move_dir[0] < 0:
                    self.facing_left = True
                elif move_dir[0] > 0:
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

    def draw_hp(self, surface, offset=(0, 0)):
        if self.hp > 0:
            bar_w = self.rect.width
            bar_h = 6 if self.is_boss else 4
            pct = self.hp / self.max_hp
            x = self.rect.x - offset[0]
            y = self.rect.y - offset[1]

            pygame.draw.rect(
                surface,
                (180, 0, 0),
                (x, y - 12, bar_w, bar_h)
            )
            pygame.draw.rect(
                surface,
                (0, 230, 0),
                (x, y - 12, int(bar_w * pct), bar_h)
            )