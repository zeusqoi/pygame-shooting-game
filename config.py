# config.py

# 게임 화면 설정
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
FPS = 60

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
import pygame
import os
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

small_font = get_font(24)
large_font = get_font(48)

kfont_small = get_kfont(20)
kfont_medium = get_kfont(28)
kfont_large = get_kfont(44)

# 사운드 리소스
SOUND_TITLE_BGM = "assets/sounds/게임시작 배경음2.mp3"
SOUND_GAME_BGM = "assets/sounds/게임시작 배경음1.mp3"