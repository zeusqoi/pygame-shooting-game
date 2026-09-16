# utils/layout.py
#
# 모든 씬의 버튼/패널 좌표는 원래 1280x800 (config.DESIGN_WIDTH/DESIGN_HEIGHT)
# 화면을 기준으로 하드코딩되어 있었습니다. 창 크기를 config.SCREEN_WIDTH/HEIGHT로
# 줄이면서, 기존 좌표를 일일이 다시 계산하지 않고 config.UI_SCALE 비율만큼
# 자동으로 축소해주는 헬퍼 함수들입니다.
#
# 사용법: 기존 pygame.Rect((x, y), (w, h)) 대신 scaled_rect(x, y, w, h)를
# 그대로 같은 숫자로 호출하면 됩니다 (숫자는 항상 1280x800 기준 "디자인 좌표").

import pygame
import config


def scaled_rect(x, y, w, h):
    """1280x800 디자인 기준 좌표/크기를 현재 화면 크기 비율로 변환합니다."""
    s = config.UI_SCALE
    return pygame.Rect(round(x * s), round(y * s), round(w * s), round(h * s))


def scaled_pos(x, y):
    """디자인 기준 좌표 한 점을 현재 화면 크기 비율로 변환합니다."""
    s = config.UI_SCALE
    return (round(x * s), round(y * s))


def scaled_size(value):
    """폰트 크기, 아이콘 한 변의 길이 등 단일 값을 현재 화면 크기 비율로 변환합니다."""
    return max(1, round(value * config.UI_SCALE))
