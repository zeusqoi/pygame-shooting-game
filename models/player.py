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
        # 기존에는 130x130으로 고정되어 있었는데, 캐릭터가 좀 더 잘 보이도록
        # 디자인 기준 크기를 170으로 키웠습니다. 창 크기(UI_SCALE)에 따라서도
        # 다른 UI 요소들처럼 같이 커지거나 작아지도록 비율을 곱해줍니다.
        _design_player_size = 170
        _scaled_player_size = max(1, round(_design_player_size * config.UI_SCALE))
        self.sprite_size = (_scaled_player_size, _scaled_player_size)

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

        # 애니메이션 처리는 항상 이 "논리적 중심 좌표"를 기준으로 합니다.
        # (공격/스킬 시 이미지가 살짝 커져도 캐릭터가 떨리거나 밀리지 않도록 중심을 고정)
        self.center_x = float(self.rect.centerx)
        self.center_y = float(self.rect.centery)

        self.is_p2 = is_p2
        # 이동 속도/공격 사거리는 화면 위 "실제 거리"에 해당하는 값이라,
        # 다른 크기/좌표들처럼 UI_SCALE을 곱해두지 않으면 창이 커졌을 때
        # (모니터가 큰 경우 등) 상대적으로 훨씬 느리고 짧게 느껴집니다.
        self.base_speed = self.char_data["speed"] * config.UI_SCALE
        self.hp = self.char_data["hp"]
        self.max_hp = self.char_data["hp"]
        self.attack_radius = self.char_data["attack_radius"] * config.UI_SCALE
        self.attack_damage = self.char_data["attack_damage"]
        self.attack_cooldown = self.char_data["attack_cooldown"]
        self.skill_duration = self.char_data["skill_duration"]
        self.skill_cooldown = self.char_data["skill_cooldown"]
        self.attack_type = self.char_data.get("attack_type", "melee")
        self.skill_type = self.char_data.get("skill_type", "speed_boost")

        # 스폰 직후에 잠깐 공격 포즈로 보이지 않도록 과거 시각으로 초기화합니다.
        self.last_attack_time = time.time() - 10
        self.skill_active = False
        self.skill_timer = 0
        self.last_skill_time = 0
        self.wants_to_use_skill = False
        self.wants_to_attack = False
        self.invincible = False
        self.last_direction = (1, 0)

        self.last_step_sound = 0
        self.step_interval = 0.25

        # 걷는 동안의 상하 바운스, 공격/스킬 시의 확대(pop) 애니메이션용 상태
        self.walk_time = 0.0
        self.bob_offset = 0.0
        self.attack_pop_duration = 0.12

        # ===================== 캐릭터별 패시브 효과 =====================
        # 메인 스킬과 별개로 항상 켜져 있는 캐릭터 개성 요소입니다.
        # - choi(최우식): 연속 공격 시 대미지가 점점 강해짐
        # - ma(마동석): 체력이 낮을수록 받는 피해가 줄어듦(맷집)
        # - gong(공유): 가만히 조준하고 있을수록(멈춰 있을수록) 대미지가 강해짐
        _passive_map = {
            "choi": "combo_damage",
            "ma": "low_hp_defense",
            "gong": "aim_focus",
        }
        self.passive_type = _passive_map.get(self.char_id)

        # combo_damage(최우식) 관련 상태
        self.combo_count = 0
        self.combo_last_time = 0.0
        self.combo_window = 2.0            # 이 시간 안에 다시 공격해야 콤보 유지
        self.combo_max_stack = 5
        self.combo_bonus_per_stack = 0.05  # 스택당 +5% 대미지 (최대 +25%)

        # aim_focus(공유) 관련 상태
        self.is_moving = False
        self.still_since = time.time()
        self.aim_focus_rate = 0.15         # 초당 증가하는 대미지 보너스
        self.aim_focus_max_bonus = 0.45    # 최대 +45% 대미지

        # ===================== 2차 능력: 대시(회피) =====================
        # 메인 스킬(F / RShift)과 별개로 짧은 쿨타임의 회피기를 하나 더 줍니다.
        # 1P는 왼쪽 Shift, 2P는 오른쪽 Ctrl로 사용하며, 대시 중에는 짧게
        # 무적이 되어 위험한 순간에 급하게 빠져나올 수 있습니다.
        self.dash_cooldown = 3.0
        self.dash_duration = 0.15
        self.dash_speed_multiplier = 8.0
        self.last_dash_time = -999.0
        self.is_dashing = False
        self.dash_timer = 0.0
        self.dash_dir = (0, 0)
        self.dash_invincible = False

    @property
    def hitbox(self):
        # 원래 130px 스프라이트 기준으로 -120px만큼 인셋(히트박스가 이미지보다
        # 훨씬 작게 잡혀 있던 밸런스)을 스프라이트 크기가 바뀌어도 그대로
        # 유지하기 위해, 고정 픽셀이 아니라 같은 비율로 인셋합니다.
        inset_ratio = 120 / 130
        inset_w = round(self.rect.width * inset_ratio)
        inset_h = round(self.rect.height * inset_ratio)
        return self.rect.inflate(-inset_w, -inset_h)

    @property
    def is_invincible(self):
        """스킬로 인한 무적(예: 마동석 스킬)과 대시로 인한 짧은 무적을
        하나로 합쳐서 확인할 수 있게 해줍니다."""
        return self.invincible or self.dash_invincible

    def register_attack(self):
        """실제로 공격이 나간 시점에 game_scene에서 호출합니다.
        연속 공격 패시브(콤보)의 스택을 갱신합니다."""
        now = time.time()
        if self.passive_type == "combo_damage":
            if now - self.combo_last_time <= self.combo_window:
                self.combo_count = min(self.combo_count + 1, self.combo_max_stack)
            else:
                self.combo_count = 1
            self.combo_last_time = now

    def get_damage_multiplier(self):
        """캐릭터별 패시브에 따라 이번 공격에 적용할 대미지 배율을 계산합니다."""
        now = time.time()

        if self.passive_type == "combo_damage":
            if now - self.combo_last_time > self.combo_window:
                self.combo_count = 0
            return 1.0 + self.combo_count * self.combo_bonus_per_stack

        if self.passive_type == "aim_focus":
            still_time = 0.0 if self.is_moving else max(0.0, now - self.still_since)
            bonus = min(self.aim_focus_max_bonus, still_time * self.aim_focus_rate)
            return 1.0 + bonus

        return 1.0

    def get_incoming_damage_multiplier(self):
        """캐릭터별 패시브에 따라 이번에 받는 피해에 적용할 배율을 계산합니다."""
        if self.passive_type == "low_hp_defense" and self.max_hp:
            missing_frac = 1.0 - (self.hp / self.max_hp)
            missing_frac = max(0.0, min(1.0, missing_frac))
            reduction = min(0.5, missing_frac * 0.5)  # 체력이 낮을수록 최대 50%까지 경감
            return 1.0 - reduction
        return 1.0

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

            dash_key = keys[pygame.K_LSHIFT]
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

            dash_key = keys[pygame.K_RCTRL]

        self.center_x += dx
        self.center_y += dy

        now = time.time()
        moving = (dx != 0 or dy != 0)
        self.is_moving = moving

        if moving:
            if now - self.last_step_sound > self.step_interval:
                play_sound("걷는 효과음.mp3", volume=0.35)
                self.last_step_sound = now

            mag = math.hypot(dx, dy)
            if mag != 0:
                self.last_direction = (dx / mag, dy / mag)

            # 이동 중에는 걸음걸이처럼 살짝 위아래로 흔들리는 바운스를 줍니다.
            self.walk_time += time_delta * 9
            self.bob_offset = math.sin(self.walk_time) * 3

            # gong 패시브(조준 강화)용 "멈춰 있던 시간" 초기화
            self.still_since = now
        else:
            self.walk_time = 0.0
            self.bob_offset *= 0.7  # 멈추면 서서히 원래 위치로 복귀

        # ===================== 대시(회피) 처리 =====================
        if dash_key and not self.is_dashing and now - self.last_dash_time > self.dash_cooldown:
            self.is_dashing = True
            self.dash_timer = now
            self.last_dash_time = now
            self.dash_invincible = True
            if moving:
                mag = math.hypot(dx, dy)
                self.dash_dir = (dx / mag, dy / mag) if mag != 0 else self.last_direction
            else:
                self.dash_dir = self.last_direction

        if self.is_dashing:
            dash_elapsed = now - self.dash_timer
            if dash_elapsed < self.dash_duration:
                dash_speed = self.base_speed * self.dash_speed_multiplier
                self.center_x += self.dash_dir[0] * dash_speed
                self.center_y += self.dash_dir[1] * dash_speed
            else:
                self.is_dashing = False
                self.dash_invincible = False

        # 대시로 화면 밖까지 튕겨 나가지 않도록 좌표를 화면 안으로 고정합니다.
        half_w, half_h = self.sprite_size[0] / 2, self.sprite_size[1] / 2
        self.center_x = min(max(self.center_x, half_w), config.SCREEN_WIDTH - half_w)
        self.center_y = min(max(self.center_y, half_h), config.SCREEN_HEIGHT - half_h)

        if self.skill_active and time.time() > self.skill_timer:
            self.skill_active = False
            self.invincible = False

        attack_elapsed = time.time() - self.last_attack_time

        if self.skill_active:
            base_image = self.img_skill
        elif attack_elapsed < 0.2:
            base_image = self.img_attack
        else:
            base_image = self.img_default

        # 공격 직후 짧게 확대되었다가 원래 크기로 돌아오는 "타격감" 팝 효과
        scale = 1.0
        if base_image is self.img_attack and attack_elapsed < self.attack_pop_duration:
            pop_progress = attack_elapsed / self.attack_pop_duration
            scale = 1.2 - 0.2 * pop_progress
        elif self.skill_active:
            # 스킬 지속 중에는 은은하게 맥동하는 효과로 활성 상태임을 알려줍니다.
            scale = 1.0 + 0.05 * math.sin(time.time() * 8)

        if abs(scale - 1.0) > 0.01:
            w, h = self.sprite_size
            new_size = (max(1, round(w * scale)), max(1, round(h * scale)))
            image = pygame.transform.smoothscale(base_image, new_size)
        else:
            image = base_image

        if self.last_direction[0] > 0:
            image = pygame.transform.flip(image, True, False)

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.centerx = round(self.center_x)
        self.rect.centery = round(self.center_y + self.bob_offset)

    def draw_hp(self, surface):
        if self.hp > 0:
            bar_w = 80
            bar_h = 8
            pct = self.hp / self.max_hp

            bar_x = self.rect.centerx - (bar_w // 2)
            bar_y = self.rect.bottom - 10

            pygame.draw.rect(surface, (180, 0, 0), (bar_x, bar_y, bar_w, bar_h))
            pygame.draw.rect(surface, (255, 255, 0), (bar_x, bar_y, int(bar_w * pct), bar_h))
