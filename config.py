# config.py

import sys
import pygame
import os

# Windows에서 디스플레이 배율(예: 125%, 150%)이 설정되어 있으면, 이 앱이
# "DPI를 스스로 처리하지 않는 옛날 프로그램"으로 인식되어 Windows가 창을 통째로
# 확대/축소해서 보여줍니다. 아래에서 모니터 실제 해상도를 기준으로 창 크기를
# 계산하기 때문에, pygame이 디스플레이를 건드리기 전에 반드시 이 설정을 먼저
# 적용해야 실제 해상도를 정확히 읽고 창도 의도한 크기로 뜹니다.
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception as e:
        print(f"[DISPLAY] Windows DPI 인식 설정 실패: {e}")

pygame.display.init()

# 게임 화면 설정
# 모든 버튼/패널 좌표는 원래 1280x800(DESIGN_WIDTH/HEIGHT) 기준으로 작성되었습니다.
# 실제 창 크기(SCREEN_WIDTH/HEIGHT)가 달라지면, UI_SCALE 비율에 맞춰
# utils/layout.py의 scaled_rect()/scaled_size()가 모든 좌표를 자동으로 늘리거나 줄여줍니다.
DESIGN_WIDTH = 1280
DESIGN_HEIGHT = 800
_DESIGN_ASPECT = DESIGN_WIDTH / DESIGN_HEIGHT  # 1.6

# 창 크기를 고정 픽셀 값으로 못박아두면 모니터 해상도에 따라 "너무 작다/크다"는
# 느낌을 계속 줄 수밖에 없습니다. 대신 실행 중인 모니터의 실제 해상도를 읽어서,
# 그 화면 세로 길이의 75% 정도(제목표시줄/작업표시줄 여유 포함)를 차지하도록
# 창 크기를 자동으로 계산합니다. 디자인 좌표(1280x800) 대비 비율은 그대로
# UI_SCALE에 반영되므로, 모니터가 작든 크든 모든 버튼/폰트가 화면에 맞게
# 비례해서 커지거나 작아집니다.
try:
    _info = pygame.display.Info()
    _desktop_w, _desktop_h = _info.current_w, _info.current_h
except Exception:
    _desktop_w, _desktop_h = 0, 0

if _desktop_w <= 0 or _desktop_h <= 0:
    _desktop_w, _desktop_h = DESIGN_WIDTH, DESIGN_HEIGHT

_target_h = int(_desktop_h * 0.75)
_target_w = int(_target_h * _DESIGN_ASPECT)

# 세로 기준으로 계산한 폭이 화면 폭의 90%를 넘으면(가로로 좁은 모니터 등)
# 폭 기준으로 다시 계산합니다.
if _target_w > _desktop_w * 0.9:
    _target_w = int(_desktop_w * 0.9)
    _target_h = int(_target_w / _DESIGN_ASPECT)

SCREEN_WIDTH = max(640, _target_w)
SCREEN_HEIGHT = max(400, _target_h)
FPS = 60

UI_SCALE = SCREEN_WIDTH / DESIGN_WIDTH

# 이미지 리소스 규칙 (현재는 임시 도형 사용하므로 경로 형식만 명시)
IMG_PLAYER_1_IDLE = ""
IMG_PLAYER_2_IDLE = ""
IMG_ZOMBIE_WALK = ""
IMG_MAIN_BG = "assets/images/main_background.png"
IMG_BG_STAGE_1 = "assets/images/ST1.jpg"
IMG_BG_STAGE_2 = "assets/images/ST2-1.png"
IMG_BG_STAGE_3 = "assets/images/ST3-1.png"
IMG_BG_STAGE_4 = "assets/images/ST4-1.png"

# 밸런스 데이터
PLAYER_SPEED = 5
PLAYER_HP_MAX = 100
PLAYER_SKILL_DURATION = 3.0 # 스킬 효과 유지 시간 (초)
PLAYER_ATTACK_RADIUS = 100 # 범위 공격 반경
PLAYER_ATTACK_DAMAGE = 10
PLAYER_ATTACK_COOLDOWN = 2.0 # 2초마다 자동 공격

ZOMBIE_BASE_HP = 10
ZOMBIE_BASE_SPEED = 1.0
ZOMBIE_DAMAGE = 1
ZOMBIE_SPAWN_RATE = 1.0 # 스폰 빈도 조절용

ITEM_DROP_RATE = 0.3
ITEM_HEAL_AMOUNT = 20

# 색상 상수
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 100, 0)
GRAY = (100, 100, 100)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
PURPLE = (255, 100, 255)

# 폰트 설정 (게임 내 렌더링용)
pygame.font.init()

# 영문/픽셀 연출용 폰트와, 한글이 실제로 지원되는 폰트를 분리해서 관리합니다.
# 기존에는 SysFont(None, size)만 사용해서 OS 기본 폰트로 대체되었는데,
# 이 기본 폰트는 한글 글리프를 지원하지 않아 한글 텍스트가 깨져 보이는 문제가 있었습니다.
FONT_PIXEL_PATH = "assets/fonts/PixelifySans.ttf"
FONT_KOREAN_PATH = "assets/fonts/AppleSDGothicNeoR.ttf"

def _load_font(path, size):
    try:
        if os.path.exists(path):
            return pygame.font.Font(path, size)
    except Exception as e:
        print(f"[FONT] {path} 로드 실패, 기본 폰트로 대체합니다: {e}")
    return pygame.font.SysFont(None, size)

def get_font(size):
    """영문/숫자 위주의 UI 텍스트용 (기존 픽셀 폰트 유지)."""
    return _load_font(FONT_PIXEL_PATH, size)

def get_kfont(size):
    """한글이 포함될 수 있는 텍스트(캐릭터 이름, 닉네임, 스킬 안내 등)에 사용합니다."""
    return _load_font(FONT_KOREAN_PATH, size)

small_font = get_font(round(24 * UI_SCALE))
large_font = get_font(round(48 * UI_SCALE))

kfont_small = get_kfont(round(20 * UI_SCALE))
kfont_medium = get_kfont(round(28 * UI_SCALE))
kfont_large = get_kfont(round(44 * UI_SCALE))

# 사운드 리소스
SOUND_TITLE_BGM = "assets/sounds/게임시작 배경음2.mp3"
SOUND_GAME_BGM = "assets/sounds/게임시작 배경음1.mp3"