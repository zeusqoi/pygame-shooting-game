# globals.py

import pygame
import os
import json
import config
from db_manager import DBManager

# Windows DPI 인식 설정과, 모니터 실제 해상도에 맞춘 SCREEN_WIDTH/HEIGHT 계산은
# 이제 config.py에서 pygame 디스플레이를 처음 건드리는 시점(가장 먼저 import되는
# 시점)에 함께 처리됩니다. 여기서는 그 결과값을 그대로 사용해 창을 띄우기만 하면
# 됩니다.
# 전역 변수 초기화
pygame.init()

_theme_src_path = "theme.json" if os.path.exists("theme.json") and os.path.exists("assets/fonts/PixelifySans.ttf") else None

if _theme_src_path:
    # theme.json에 박혀있는 폰트 크기/테두리/패딩 같은 값들은 원래 UI_SCALE과
    # 무관하게 고정 픽셀이었습니다. 그래서 창이 커지면(모니터 해상도가 커서
    # SCREEN_WIDTH/HEIGHT가 커지면) 박스/버튼 같은 레이아웃은 UI_SCALE만큼
    # 커지는데 글씨/테두리는 그대로라 "박스는 큰데 글씨는 작고 여백만 남는"
    # 불균형이 생겼습니다. utils/theme_scale.py로 UI_SCALE만큼 스케일링한
    # theme.json을 만들어서 그걸 대신 씁니다.
    from utils.theme_scale import build_scaled_theme
    theme_path = build_scaled_theme(_theme_src_path, config.UI_SCALE)
else:
    theme_path = None

# 창 크기는 config.SCREEN_WIDTH/HEIGHT (모니터 해상도에 맞춰 자동 계산됨) 그대로 사용합니다.
# 참고: 이전에 pygame.SCALED 플래그를 함께 썼었는데, SCALED는 요청한 해상도가
# 데스크톱보다 작을 때 오히려 창을 데스크톱에 맞춰 "확대"해버리는 경우가 있어서
# (모니터에 따라 창이 다시 커지고 화면 하단이 잘리는 문제 발생), SCALED 없이
# config.py가 계산한 크기 그대로 창을 띄웁니다.
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

# ---------------------------------------------------------
# 배경 이미지
# ---------------------------------------------------------
# 기존에는 고해상도 사진 배경(main_background.png, ST1.jpg 등)을 그대로 화면에
# 꽉 채워서 사용했는데, 화면이 너무 빽빽하고 무겁게 느껴진다는 피드백이 있어서
# 우선 코드로 만든 간결한 그라데이션 배경으로 대체했습니다.
# 나중에 새 배경 이미지 파일이 준비되면, 아래 gradient 대신
# `pygame.image.load(경로).convert()` 로 다시 교체하면 됩니다
# (기존 assets/images/main_background.png, ST1.jpg 등 파일 자체는 그대로 남아있습니다).
from utils.ui_utils import generate_gradient_surface

_screen_size = (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)

main_bg_img = generate_gradient_surface(_screen_size, (18, 22, 34), (38, 46, 70))

stage_bg_imgs = {
    1: generate_gradient_surface(_screen_size, (24, 46, 26), (10, 18, 12)),   # 스테이지 1: 차분한 녹색
    2: [generate_gradient_surface(_screen_size, (52, 40, 18), (18, 14, 8))],  # 스테이지 2: 저물녘 갈색
    4: generate_gradient_surface(_screen_size, (48, 18, 18), (16, 6, 6)),     # 스테이지 3(보스1): 붉은 경고감
    5: generate_gradient_surface(_screen_size, (30, 14, 40), (10, 6, 16)),    # 스테이지 4(최종 보스): 보라빛 긴장감
}

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