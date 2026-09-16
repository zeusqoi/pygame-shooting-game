# globals.py

import pygame
import os
import json
import config
from db_manager import DBManager

# 전역 변수 초기화
pygame.init()

theme_path = "theme.json" if os.path.exists("theme.json") and os.path.exists("assets/fonts/PixelifySans.ttf") else None
screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
pygame.display.set_caption("마곡행 (Train to Magok)")
clock = pygame.time.Clock()

db = DBManager()
current_user = "Guest"

# 폰트 (이미 config.py에서 초기화됨)
# config.small_font = config.small_font (기존 값 유지)

# 캐릭터 데이터 로드
try:
    if os.path.exists('character_data.json'):
        with open('character_data.json', 'r', encoding='utf-8') as f:
            CHAR_DATA = json.load(f)["characters"]
    else:
        raise FileNotFoundError("character_data.json not found")
except Exception as e:
    print(f"캐릭터 데이터 로드 실패: {e}")
    CHAR_DATA = {
        "choi": {
            "name": "최우식", "hp": 100, "speed": 5, "attack_type": "melee",
            "attack_radius": 120, "attack_damage": 10, "attack_cooldown": 2.0,
            "skill_type": "homerun", "skill_duration": 1.0, "skill_cooldown": 8.0
        }
    }

main_bg_img = None
try:
    path = getattr(config, 'IMG_MAIN_BG', "")
    if path and os.path.exists(path):
        main_bg_img = pygame.image.load(path).convert()
except Exception as e:
    print(f"메인 배경 로드 실패: {e}")

# 기존 stage_bg_imgs 부분 교체
stage_bg_imgs = {1: None, 2: [], 4: None, 5: None}

try:
    path = "assets/images/ST1.jpg"
    print("현재 cwd:", os.getcwd())          # ← 추가
    print("절대 경로:", os.path.abspath(path))  # ← 추가
    print("파일 존재:", os.path.exists(path))   # ← 추가
    if os.path.exists(path):
        stage_bg_imgs[1] = pygame.image.load(path).convert()

    for i in range(1, 5):
        path = f"assets/images/ST2-{i}.png"
        if os.path.exists(path):
            stage_bg_imgs[2].append(pygame.image.load(path).convert())

    for key, attr in [(4, 'IMG_BG_STAGE_3'), (5, 'IMG_BG_STAGE_4')]:
        path = getattr(config, attr, "")
        if path and os.path.exists(path):
            stage_bg_imgs[key] = pygame.image.load(path).convert()

except Exception as e:
    print(f"스테이지 배경 로드 실패: {e}")

# ✅ 좀비 스프라이트 로드 (z1~z4, 각 1~4프레임)
# z1=soldier, z2=explode, z3=mutant, z4=ranged
zombie_imgs = {}
for z_key, z_name in [("soldier","z1"), ("explode","z2"), ("mutant","z3"), ("ranged","z4")]:
    frames = []
    for i in range(1, 5):
        path = f"assets/images/{z_name}-{i}.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                frames.append(img)
            except:
                pass
    if frames:
        zombie_imgs[z_key] = frames

# ✅ 보스 스프라이트 로드 (boss1~6프레임, boss2~6프레임)
boss_imgs = {}
for b_key, b_name in [("boss1","boss1"), ("boss2","boss2")]:
    frames = []
    for i in range(1, 7):
        path = f"assets/images/{b_name}-{i}.png"
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                frames.append(img)
            except:
                pass
    if frames:
        boss_imgs[b_key] = frames

hp_bar_imgs = {}
for i in range(7):
    path = f"assets/images/hp{i}.png"
    if os.path.exists(path):
        try:
            hp_bar_imgs[i] = pygame.image.load(path).convert_alpha()
        except:
            pass

stage_start_imgs = {}
for i in range(1, 6):
    path = f"assets/images/stage_{i}.png"
    if os.path.exists(path):
        try:
            stage_start_imgs[i] = pygame.image.load(path).convert()
        except:
            pass

gameover_img = None
try:
    path = "assets/images/GAMEOVER.png"
    if os.path.exists(path):
        gameover_img = pygame.image.load(path).convert()
    else:
        print(f"게임오버 이미지 없음: {path}")
except Exception as e:
    print(f"게임오버 이미지 로드 실패: {e}")

def set_current_user(user):
    global current_user
    current_user = user