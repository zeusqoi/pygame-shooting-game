# game_scene.py

import pygame
import time
import random
import math
import os
import config
import pygame_gui
from core.globals import stage_bg_imgs, db
import core.globals as g
from core.scene_manager import Scene
from models.player import Player
from models.zombie import Zombie
from models.projectile import Projectile
from models.ranged_projectile import RangedProjectile

from models.effects import AttackEffect, HitEffect
from models.item import Item
from utils.sound_manager import play_sound, stop_channel, play_music

# 스테이지별 설정
STAGE_CONFIG = {
    1: {
        "bg_key": 1,
        "zombie_types": ["soldier"],
        "kill_goal": 30,
        "boss_stage": False,
        "spawn_interval": 2.0,
    },
    2: {
        "bg_key": 2,
        "zombie_types": ["soldier", "explode", "mutant", "ranged"],
        "kill_goal": 40,
        "boss_stage": False,
        "spawn_interval": 1.5,
    },
    3: {
        "bg_key": 4,
        "zombie_types": ["soldier", "explode", "mutant", "ranged", "boss1"],
        "kill_goal": None,
        "boss_stage": True,
        "boss_type": "boss1",
        "spawn_interval": 2.0,
    },
    4: {
        "bg_key": 5,
        "zombie_types": ["soldier", "explode", "mutant", "ranged", "boss2"],
        "kill_goal": None,
        "boss_stage": True,
        "boss_type": "boss2",
        "spawn_interval": 1.8,
    },
}


class GameScene(Scene):
    def __init__(self, players=1, p1_char="choi", p2_char="choi"):
        super().__init__()

        self.all_sprites = pygame.sprite.Group()
        self.zombies = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        self.effects = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.players = []
        self.num_players = players

        self.ma_skill_channels = {}

        p1 = Player(char_id=p1_char, is_p2=False)
        self.all_sprites.add(p1)
        self.players.append(p1)

        if players == 2:
            p2 = Player(char_id=p2_char, is_p2=True)
            self.all_sprites.add(p2)
            self.players.append(p2)

        self.stage = 1
        self.kills = 0
        self.boss_spawned = False
        self.boss_killed = False
        self.last_spawn_time = time.time()
        self.paused = False
        self.kills = 0          # ✅ 총 누적 킬수
        self.stage_kills = 0    # ✅ 현재 스테이지 킬수

        self.stage_intro_timer = 1.0
        self.showing_stage_intro = True

        self.bg_scroll_x = 0
        self.bg_scroll_speed = 2
        self.current_bg = None
        self.bg_change_timer = 0
        self.st2_bg_index = 0
        self._pick_random_bg()

        self.stage_clear_timer = None
        self.stage_clear_msg = ""

        # =========================
        # 최종 보스 WARNING 연출
        # =========================
        self.show_boss_warning = False
        self.boss_warning_timer = 0.0
        self.pending_boss_type = None
        self.boss_warning_duration = 2.0
        self.shake_timer = 0.0
        self.shake_intensity = 0

        self.warning_img = None
        warning_path = "assets/images/warning.png"
        if os.path.exists(warning_path):
            try:
                self.warning_img = pygame.image.load(warning_path).convert_alpha()
                self.warning_img = pygame.transform.scale(self.warning_img, (520, 300))
            except Exception as e:
                print("WARNING 이미지 로드 실패:", e)

        self._play_stage_start_sound()
        print("stage =", self.stage)
        print("bg =", self.current_bg)

        try:
            play_music(config.SOUND_GAME_BGM, volume=0.5)
        except Exception as e:
            print("게임 배경음 실행 실패:", e)

        from core.globals import theme_path
        self.ui_manager = pygame_gui.UIManager((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), theme_path)
        self.btn_pause = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((config.SCREEN_WIDTH - 110, 10), (100, 40)),
            text="PAUSE",
            manager=self.ui_manager,
            object_id="@dark_btn"
        )

        self.btn_exit = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((config.SCREEN_WIDTH // 2 - 100, config.SCREEN_HEIGHT // 2 + 50), (200, 50)),
            text="EXIT TO MAIN",
            manager=self.ui_manager,
            object_id="@dark_btn"
        )
        self.btn_exit.hide()

    def _reset_boss_warning(self):
        self.show_boss_warning = False
        self.boss_warning_timer = 0.0
        self.pending_boss_type = None

    def _toggle_pause(self):
        self.paused = not self.paused
        self.btn_pause.set_text("RESUME" if self.paused else "PAUSE")
        if self.paused:
            self.btn_exit.show()
        else:
            self.btn_exit.hide()

    def _pick_random_bg(self):
        print("stage:", self.stage)
        print("stage_bg_imgs[1]:", stage_bg_imgs[1])

        if self.stage == 1 and stage_bg_imgs[1]:
            print("ST1 배경 설정")
            self.current_bg = stage_bg_imgs[1]
            self.bg_change_timer = 999

        elif self.stage == 2 and stage_bg_imgs[2]:
            self.current_bg = stage_bg_imgs[2][self.st2_bg_index % len(stage_bg_imgs[2])]
            self.bg_change_timer = 20.0

        else:
            bg_key = {1: 1, 2: 2, 3: 4, 4: 5}.get(self.stage, 1)
            self.current_bg = stage_bg_imgs.get(bg_key)
            self.bg_change_timer = 999
            print("current_bg =", self.current_bg)

    def _stage_cfg(self):
        return STAGE_CONFIG.get(self.stage, STAGE_CONFIG[1])

    def _player_key(self, player):
        candidates = [
            getattr(player, "char_id", ""),
            player.char_data.get("name", "")
        ]
        raw = " ".join([str(x).lower() for x in candidates if x])

        if any(key in raw for key in ["gong", "gongyu", "공유"]):
            return "gong"
        if any(key in raw for key in ["ma", "madongseok", "마동석"]):
            return "ma"
        if any(key in raw for key in ["choi", "choiwoosik", "choi_woosik", "최우식"]):
            return "choi"

        return raw

    def _play_player_attack_sound(self, player):
        sound_map = {
            "gong": "공유 기본 효과음.mp3",
            "ma": "마동석 기본 효과음.mp3",
            "choi": "최우식 일반 공격 효과음.mp3",
        }
        sound = sound_map.get(self._player_key(player))
        if sound:
            play_sound(sound, volume=0.55)

    def _start_ma_skill_loop(self, player):
        key = id(player)
        old_channel = self.ma_skill_channels.get(key)

        if old_channel is not None and old_channel.get_busy():
            return

        channel = play_sound("마동석 궁극기 효과음.mp3", volume=0.8, loops=-1)
        self.ma_skill_channels[key] = channel

    def _stop_ma_skill_loop(self, player):
        key = id(player)
        channel = self.ma_skill_channels.get(key)

        if channel is not None:
            stop_channel(channel)
            self.ma_skill_channels[key] = None

    def _play_player_skill_sound(self, player):
        key = self._player_key(player)

        if key == "ma":
            self._start_ma_skill_loop(player)
            return

        sound_map = {
            "gong": "공유 궁극기 효과음.mp3",
            "choi": "최우식 궁극기 효과음.mp3",
        }
        sound = sound_map.get(key)
        if sound:
            play_sound(sound, volume=0.8)

    def _play_stage_start_sound(self):
        sound_map = {
            1: "스테이지 1 시작.mp3",
            2: "스테이지 2 시작할때.mp3",
            3: "스테이지 3 시작할때.mp3",
            4: "마지막 스테이지 시작할 때.mp3",
        }
        sound = sound_map.get(self.stage)
        if sound:
            play_sound(sound, volume=1.0)

    def _play_zombie_hit_sound(self):
        play_sound(
            random.choice([
                "좀비 맞았을 때 나는 소리 1.mp3",
                "좀비 맞았을 때 나는 소리2.mp3",
            ]),
            volume=0.35
        )

    def _stop_all_ma_skill_loops(self):
        for channel in self.ma_skill_channels.values():
            if channel is not None:
                stop_channel(channel)
        self.ma_skill_channels = {}

    def _next_stage(self):
        if self.stage < 4:
            self._stop_all_ma_skill_loops()
            self._reset_boss_warning()

            self.stage += 1
            self.stage_kills = 0  # 스테이지 킬만 리셋, 총 킬은 유지
            self.boss_spawned = False
            self.boss_killed = False
            self.bg_scroll_x = 0
            self._pick_random_bg()
            self._play_stage_start_sound()
            self.stage_intro_timer = 1.0
            self.showing_stage_intro = True

            for player in self.players:
                # 1. 공통: 최대 체력 100 증가 및 체력 완전 회복
                player.max_hp += 100
                player.hp = player.max_hp

                # 2. 캐릭터별 고유 능력치 성장
                p_key = self._player_key(player)
                if p_key == "ma":
                    # 마동석: 공격 범위 크게 증가
                    player.attack_radius += 30
                elif p_key == "choi":
                    # 최우식: 공격 범위 크게 증가
                    player.attack_radius += 30
                elif p_key == "gong":
                    # 공유: 공격 쿨타임 감소 (최소 0.1초 보장)
                    player.attack_cooldown = max(0.1, player.attack_cooldown - 0.1)

            for z in list(self.zombies):
                z.kill()

            for item in list(self.items):
                item.kill()
                
        else:
            self._stop_all_ma_skill_loops()
            self._reset_boss_warning()
            pygame.mixer.music.stop()
            db.save_score(self.kills, username=g.current_user)
            from scenes.ending_scene import EndingScene
            self.manager.switch_to(EndingScene(self.kills))

    def handle_events(self, events):
        for e in events:
            self.ui_manager.process_events(e)
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    self._toggle_pause()

                # 1P 공격
                if e.key == pygame.K_SPACE:
                    if len(self.players) > 0:
                        self.players[0].wants_to_attack = True

                # 테스트용 스테이지 전환
                if e.key in (pygame.K_1, pygame.K_KP1):
                    self._stop_all_ma_skill_loops()
                    self._reset_boss_warning()
                    self.stage = 1
                    self.boss_spawned = False
                    self.boss_killed = False
                    self._pick_random_bg()
                    self._play_stage_start_sound()

                elif e.key in (pygame.K_2, pygame.K_KP2):
                    self._stop_all_ma_skill_loops()
                    self._reset_boss_warning()
                    self.stage = 2
                    self.boss_spawned = False
                    self.boss_killed = False
                    self.st2_bg_index = 0
                    self._pick_random_bg()
                    self._play_stage_start_sound()

                elif e.key in (pygame.K_3, pygame.K_KP3):
                    self._stop_all_ma_skill_loops()
                    self._reset_boss_warning()
                    self.stage = 3
                    self.boss_spawned = False
                    self.boss_killed = False
                    self._pick_random_bg()
                    self._play_stage_start_sound()

                elif e.key in (pygame.K_4, pygame.K_KP4):
                    self._stop_all_ma_skill_loops()
                    self._reset_boss_warning()
                    self.stage = 4
                    self.boss_spawned = False
                    self.boss_killed = False
                    self._pick_random_bg()
                    self._play_stage_start_sound()

            # 2P 공격
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    if self.num_players == 2 and len(self.players) > 1:
                        self.players[1].wants_to_attack = True

            if e.type == pygame_gui.UI_BUTTON_PRESSED:
                if e.ui_element == self.btn_pause:
                    self._toggle_pause()
                elif e.ui_element == self.btn_exit:
                    from scenes.title_scene import TitleScene
                    self.manager.switch_to(TitleScene())

    def update(self, time_delta):
        if self.shake_timer > 0:
            self.shake_timer -= time_delta
            if self.shake_timer <= 0:
                self.shake_intensity = 0
        if self.showing_stage_intro:
            self.stage_intro_timer -= time_delta
            if self.stage_intro_timer <= 0:
                self.showing_stage_intro = False
            return

        if hasattr(self, "ui_manager"):
            self.ui_manager.update(time_delta)

        # 최종 보스 WARNING 표시 중
        if self.show_boss_warning:
            self.boss_warning_timer -= time_delta
            if self.boss_warning_timer <= 0:
                z = Zombie(self.stage, self.players, zombie_type=self.pending_boss_type)
                self.all_sprites.add(z)
                self.zombies.add(z)
                self.boss_spawned = True

                self.show_boss_warning = False
                self.pending_boss_type = None

            return

        if self.paused:
            return

        cfg = self._stage_cfg()

        if self.stage != 1:
            self.bg_scroll_x -= self.bg_scroll_speed

        self.bg_change_timer -= time_delta
        if self.bg_change_timer <= 0:
            if self.stage == 2:
                self.st2_bg_index += 1
            self._pick_random_bg()

        # if self.stage == 1:
        #     self.bg_change_timer -= time_delta
        #     if self.bg_change_timer <= 0:
        #         self._pick_random_bg()

        self.all_sprites.update(time_delta)
        self.effects.update(time_delta)
        self.enemy_projectiles.update(time_delta)

        now = time.time()
        spawn_interval = cfg["spawn_interval"] / max(self.stage * 0.5, 1)

        if now - self.last_spawn_time > spawn_interval:
            available = list(cfg["zombie_types"])

            if cfg["boss_stage"]:
                boss_type = cfg["boss_type"]

                if not self.boss_spawned:
                    # 최종 보스 boss2는 WARNING 먼저 출력
                    if boss_type == "boss2":
                        if not self.show_boss_warning and self.pending_boss_type is None:
                            play_sound("보스 나오기 전 효과음.mp3", volume=0.7)
                            self.show_boss_warning = True
                            self.boss_warning_timer = self.boss_warning_duration
                            self.pending_boss_type = boss_type
                            self.last_spawn_time = now
                            return
                    else:
                        play_sound("보스 나오기 전 효과음.mp3", volume=0.7)
                        z = Zombie(self.stage, self.players, zombie_type=boss_type)
                        self.all_sprites.add(z)
                        self.zombies.add(z)
                        self.boss_spawned = True

                normal_types = [t for t in available if t not in ["boss1", "boss2"]]
                if normal_types and not self.show_boss_warning and self.pending_boss_type is None:
                    z = Zombie(
                        self.stage,
                        self.players,
                        zombie_type=random.choice(normal_types)
                    )
                    self.all_sprites.add(z)
                    self.zombies.add(z)

            else:
                z = Zombie(
                    self.stage,
                    self.players,
                    zombie_type=random.choice(available)
                )
                self.all_sprites.add(z)
                self.zombies.add(z)

            self.last_spawn_time = now

        for z in self.zombies:
            if z.zombie_type == "ranged":
                closest_p = min(
                    (p for p in self.players if p.hp > 0),
                    key=lambda p: math.hypot(
                        p.rect.centerx - z.rect.centerx,
                        p.rect.centery - z.rect.centery
                    ),
                    default=None
                )

                if closest_p:
                    dist = math.hypot(
                        closest_p.rect.centerx - z.rect.centerx,
                        closest_p.rect.centery - z.rect.centery
                    )

                    if dist < z.ranged_range and now - z.last_ranged_attack > z.ranged_cooldown:
                        proj = RangedProjectile(
                            z.rect.center,
                            closest_p.rect.center,
                            damage=z.damage,
                            speed=5
                        )
                        self.enemy_projectiles.add(proj)
                        z.last_ranged_attack = now

        # 플레이어 스킬 & 수동 공격
        for p in list(self.players):
            if self._player_key(p) == "ma" and not p.skill_active:
                self._stop_ma_skill_loop(p)

            if p.wants_to_use_skill:
                p.wants_to_use_skill = False
                p.last_skill_time = now
                p.skill_active = True
                p.skill_timer = now + p.skill_duration

                self._play_player_skill_sound(p)

                if p.skill_type == "homerun":
                    target_pos = (
                        p.rect.centerx + p.last_direction[0] * 100,
                        p.rect.centery + p.last_direction[1] * 100
                    )
                    proj = Projectile(
                        p.rect.center,
                        target_pos,
                        damage=p.attack_damage * 5,
                        speed=15,
                        is_homerun=True
                    )
                    self.all_sprites.add(proj)
                    self.projectiles.add(proj)

                elif p.skill_type == "invincible_knockback":
                    p.invincible = True
                    for z in self.zombies:
                        dist = math.hypot(
                            p.rect.centerx - z.rect.centerx,
                            p.rect.centery - z.rect.centery
                        )
                        if 0 < dist < 400:
                            z.pos_x += ((z.rect.centerx - p.rect.centerx) / dist) * 200
                            z.pos_y += ((z.rect.centery - p.rect.centery) / dist) * 200
                            z.rect.x = int(z.pos_x)
                            z.rect.y = int(z.pos_y)

            atk_cd = p.attack_cooldown
            if p.skill_type == "buff_x2" and p.skill_active:
                atk_cd /= 2.0

            if p.wants_to_attack and now - p.last_attack_time > atk_cd:
                p.wants_to_attack = False

                if p.attack_type in ["melee", "melee_knockback"]:
                    self.effects.add(AttackEffect(p.rect.center, p.attack_radius))
                    self._play_player_attack_sound(p)

                    for z in list(self.zombies):
                        dist = math.hypot(
                            p.rect.centerx - z.rect.centerx,
                            p.rect.centery - z.rect.centery
                        )

                        # 좀비의 hitbox 절반 크기만큼 공격 범위를 넓혀서 쉽게 맞도록 함
                        if dist <= p.attack_radius + (z.hitbox.width / 2):
                            z.hp -= p.attack_damage
                            self._play_zombie_hit_sound()
                            self.effects.add(HitEffect(z.rect.center))

                            if p.attack_type == "melee_knockback" and dist > 0:
                                z.pos_x += ((z.rect.centerx - p.rect.centerx) / dist) * 50
                                z.pos_y += ((z.rect.centery - p.rect.centery) / dist) * 50
                                z.rect.x = int(z.pos_x)
                                z.rect.y = int(z.pos_y)

                            if z.hp <= 0:
                                self._on_zombie_kill(z)

                elif p.attack_type == "projectile":
                    nearest_z = min(
                        self.zombies,
                        key=lambda z: math.hypot(
                            p.rect.centerx - z.rect.centerx,
                            p.rect.centery - z.rect.centery
                        ),
                        default=None
                    )

                    if nearest_z:
                        self._play_player_attack_sound(p)
                        proj = Projectile(
                            p.rect.center,
                            nearest_z.rect.center,
                            damage=p.attack_damage,
                            speed=10
                        )
                        self.all_sprites.add(proj)
                        self.projectiles.add(proj)

                p.last_attack_time = now

            elif p.wants_to_attack:
                p.wants_to_attack = False

        for proj in list(self.projectiles):
            hits = pygame.sprite.spritecollide(
                proj, self.zombies, False,
                collided=lambda p_obj, z_obj: p_obj.rect.colliderect(z_obj.hitbox)
            )

            for z in hits:
                z.hp -= proj.damage
                self._play_zombie_hit_sound()
                self.effects.add(HitEffect(z.rect.center))

                if z.hp <= 0:
                    self._on_zombie_kill(z)

                if not proj.is_homerun:
                    proj.kill()
                    break

        for proj in list(self.enemy_projectiles):
            for p in list(self.players):
                if p.invincible:
                    continue

                if proj.rect.colliderect(p.hitbox):
                    p.hp -= proj.damage
                    play_sound("좀비한테 맞았을 때 효과음.wav", volume=0.55)
                    self.effects.add(HitEffect(p.rect.center))
                    proj.kill()

                    if p.hp <= 0:
                        if self._player_key(p) == "ma":
                            self._stop_ma_skill_loop(p)
                        p.kill()
                        self.players.remove(p)
                    break

        for p in self.players:
            eaten_items = pygame.sprite.spritecollide(p, self.items, True)

            for item in eaten_items:
                p.hp = min(p.max_hp, p.hp + config.ITEM_HEAL_AMOUNT)
                play_sound("아이템 먹는 효과음.mp3", volume=0.5)

        for p in list(self.players):
            if p.invincible:
                continue

            hits = pygame.sprite.spritecollide(
                p, self.zombies, False,
                collided=lambda s1, s2: s1.hitbox.colliderect(s2.damage_hitbox)
            )
            if hits:
                p.hp -= config.ZOMBIE_DAMAGE
                play_sound("좀비한테 맞았을 때 효과음.wav", volume=0.55)
                self.effects.add(HitEffect(p.rect.center))

                if p.hp <= 0:
                    if self._player_key(p) == "ma":
                        self._stop_ma_skill_loop(p)
                    p.kill()
                    self.players.remove(p)

        if len(self.players) == 0:
            self._stop_all_ma_skill_loops()
            self._reset_boss_warning()
            db.save_score(self.kills, username=g.current_user)
            from scenes.game_over_scene import GameOverScene
            self.manager.switch_to(GameOverScene(self.kills, cleared=False))
            return

        cfg = self._stage_cfg()
        if cfg["boss_stage"]:
            if self.boss_spawned and self.boss_killed:
                self.boss_killed = False
                self._next_stage()
        else:
            if self.stage_kills >= cfg["kill_goal"]:  # ✅ stage_kills로 변경
                self._next_stage()

    def _on_zombie_kill(self, z):
        if z.is_boss:
            self.boss_killed = True
            play_sound("보스좀비가 죽었을 때 효과음.wav", volume=0.7)

        self.kills += 1        # ✅ 총 킬 누적
        self.stage_kills += 1  # ✅ 스테이지 킬 누적

        if random.random() < config.ITEM_DROP_RATE:
            item = Item(z.rect.center)
            self.all_sprites.add(item)
            self.items.add(item)

        z.kill()

        for z in self.zombies:
            if z.is_boss and getattr(z, 'is_enraged', False):
                self.shake_timer = 0.3  # 0.3초 흔들림
                self.shake_intensity = 6
                break

    def draw(self, screen):
        # 1. 흔들림 오프셋
        shake_x = random.randint(-self.shake_intensity, self.shake_intensity) if self.shake_intensity > 0 else 0
        shake_y = random.randint(-self.shake_intensity, self.shake_intensity) if self.shake_intensity > 0 else 0

        # 2. 임시 서피스에 게임 화면 그리기
        temp_surf = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        bg_img = self.current_bg
        if bg_img:
            bg_h = bg_img.get_height()
            scaled_w = int(bg_img.get_width() * (config.SCREEN_HEIGHT / bg_h))
            scaled_img = pygame.transform.scale(bg_img, (scaled_w, config.SCREEN_HEIGHT))

            if self.stage == 1:
                scaled_img = pygame.transform.scale(
                    bg_img,
                    (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
                )
                temp_surf.blit(scaled_img, (0, 0))

            else:
                x = int(self.bg_scroll_x) % scaled_w
                temp_surf.blit(scaled_img, (x - scaled_w, 0))
                temp_surf.blit(scaled_img, (x, 0))

                if x + scaled_w < config.SCREEN_WIDTH:
                    temp_surf.blit(scaled_img, (x + scaled_w, 0))

        else:
            colors = {1: (50, 100, 50), 2: (50, 50, 80), 3: (80, 40, 40), 4: (40, 0, 60)}
            temp_surf.fill(colors.get(self.stage, (30, 30, 30)))

        self.all_sprites.draw(temp_surf)
        self.effects.draw(temp_surf)
        self.enemy_projectiles.draw(temp_surf)
        for z in self.zombies:
            z.draw_hp(temp_surf)

        # 3. 흔들림 적용
        screen.fill((0, 0, 0))
        screen.blit(temp_surf, (shake_x, shake_y))

        # 4. 보스 분노 효과
        for z in self.zombies:
            if z.is_boss and getattr(z, 'is_enraged', False):
                red_overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
                red_overlay.fill((255, 0, 0, 40))
                screen.blit(red_overlay, (0, 0))
                pygame.draw.rect(screen, (255, 0, 0), (0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT), 8)
                break

        # 5. 일시정지 오버레이
        if self.paused:
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))
            txt = config.small_font.render("[ PAUSED ]  ESC to Resume", True, config.WHITE)
            screen.blit(txt, (config.SCREEN_WIDTH // 2 - txt.get_width() // 2, config.SCREEN_HEIGHT // 2))

        # 6. HUD
        from core.globals import hp_bar_imgs
        if self.players:
            p1 = self.players[0]
            hp_ratio = p1.hp / p1.max_hp
            hp_index = max(0, min(6, round(hp_ratio * 6)))
            if hp_index in hp_bar_imgs:
                hp_img = pygame.transform.scale(hp_bar_imgs[hp_index], (400, 60))
                screen.blit(hp_img, (15, 15))
            p1_hp_txt = config.small_font.render(f"1P HP: {p1.hp}", True, config.WHITE)
            screen.blit(p1_hp_txt, (425, 25))

        cfg = self._stage_cfg()
        stage_label = {1: "ST1", 2: "ST2", 3: "ST4", 4: "ST5"}
        goal_text = "BOSS" if cfg["boss_stage"] else f"Kill: {self.stage_kills}/{cfg['kill_goal']}"
        info_str = f"{stage_label.get(self.stage, 'ST?')} | {goal_text}"
        info_txt = config.small_font.render(info_str, True, config.WHITE)
        screen.blit(info_txt, (425, 55))

        if self.num_players == 2 and len(self.players) > 1:
            p2 = self.players[1]
            hp_ratio_2 = p2.hp / p2.max_hp
            idx_2 = max(0, min(6, round(hp_ratio_2 * 6)))
            if idx_2 in hp_bar_imgs:
                hp_img_2 = pygame.transform.scale(hp_bar_imgs[idx_2], (400, 60))
                screen.blit(hp_img_2, (15, 90))
            p2_txt = config.small_font.render(f"2P HP: {p2.hp}", True, config.WHITE)
            screen.blit(p2_txt, (425, 105))

        ctrl_msg = (
            "1P: WASD + SPACE + F | 2P: Arrows + Left Click"
            if self.num_players == 2
            else "Move: WASD | Attack: SPACE | Skill: F"
        )
        ctrl = config.small_font.render(ctrl_msg, True, config.WHITE)
        screen.blit(ctrl, (15, config.SCREEN_HEIGHT - 35))

        # 7. 스킬 쿨타임 UI
        for i, p in enumerate(self.players):
            icon_size = 60
            x_pos = config.SCREEN_WIDTH - 80 - (i * 90)
            icon_rect = pygame.Rect(x_pos, config.SCREEN_HEIGHT - 85, icon_size, icon_size)
            pygame.draw.rect(screen, (50, 50, 50), icon_rect)
            pygame.draw.rect(screen, config.WHITE, icon_rect, 2)
            skill_txt = config.kfont_small.render("스킬", True, config.WHITE)
            screen.blit(skill_txt, (icon_rect.centerx - skill_txt.get_width() // 2, icon_rect.centery - skill_txt.get_height() // 2 - 10))

            now = time.time()
            elapsed = now - p.last_skill_time
            if elapsed < p.skill_cooldown:
                ratio = elapsed / p.skill_cooldown
                shadow = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                cx, cy = icon_size / 2, icon_size / 2
                radius = icon_size * math.sqrt(2)
                points = [(cx, cy)]
                start_angle = -math.pi / 2 + ratio * 2 * math.pi
                end_angle = 3 * math.pi / 2
                steps = 30
                if start_angle < end_angle:
                    for j in range(steps + 1):
                        angle = start_angle + (end_angle - start_angle) * (j / steps)
                        x = cx + math.cos(angle) * radius
                        y = cy + math.sin(angle) * radius
                        points.append((x, y))
                    pygame.draw.polygon(shadow, (0, 0, 0, 180), points)
                screen.blit(shadow, icon_rect.topleft)
                remain = p.skill_cooldown - elapsed
                cd_txt = config.small_font.render(f"{remain:.1f}", True, config.YELLOW)
                screen.blit(cd_txt, (icon_rect.centerx - cd_txt.get_width() // 2, icon_rect.centery - cd_txt.get_height() // 2 + 10))
            else:
                ready_txt = config.small_font.render("READY", True, config.GREEN)
                screen.blit(ready_txt, (icon_rect.centerx - ready_txt.get_width() // 2, icon_rect.centery - ready_txt.get_height() // 2 + 10))

            p_label = f"P{i+1}"
            k_label = "F" if i == 0 else "Shift"
            p_info_txt = config.small_font.render(f"{p_label} ({k_label})", True, config.WHITE)
            screen.blit(p_info_txt, (icon_rect.centerx - p_info_txt.get_width() // 2, icon_rect.bottom + 5))

        # 8. 스테이지 인트로
        if self.showing_stage_intro:
            from core.globals import stage_start_imgs
            img_key = {1: 1, 2: 2, 3: 3, 4: 4}.get(self.stage, 1)
            img = stage_start_imgs.get(img_key)
            if img:
                scaled = pygame.transform.scale(img, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
                screen.blit(scaled, (0, 0))

        # 9. WARNING 오버레이
        if self.show_boss_warning:
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            screen.blit(overlay, (0, 0))
            if self.warning_img:
                warning_rect = self.warning_img.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2))
                screen.blit(self.warning_img, warning_rect)
            big_font = config.get_font(42)
            txt = big_font.render("FINAL BOSS WARNING", True, (255, 255, 255))
            txt_rect = txt.get_rect(center=(config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2 + 190))
            screen.blit(txt, txt_rect)

        # 10. UI Manager
        if hasattr(self, "ui_manager"):
            self.ui_manager.draw_ui(screen)