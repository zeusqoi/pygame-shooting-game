# utils/level_layout.py
"""
스테이지마다 월드(WORLD_WIDTH x WORLD_HEIGHT) 안에 장애물을 무작위로 배치해서,
매번 조금씩 다른 맵 배치가 나오도록 합니다. 완전 무작위지만 아래 두 규칙으로
"부자연스럽게" 막히는 상황을 방지합니다:

1. 맵 한가운데(플레이어 스폰 지점) 주변은 항상 비워둔다 -> 시작하자마자
   장애물에 끼이는 일이 없도록.
2. 장애물끼리는 최소 간격을 두고 배치한다 -> 장애물이 다닥다닥 붙어서
   좀비/플레이어가 지나갈 틈이 아예 없는 "막힌 벽"이 생기지 않도록.
"""

import random
import config
from models.obstacle import Obstacle


def generate_obstacles(stage, count=None, protect_points=None):
    """이번 스테이지에 사용할 Obstacle 리스트를 새로 만들어 반환합니다.

    protect_points: 장애물이 겹치면 안 되는 지점들(월드 좌표) 목록. 기본값은
    맵 중앙(최초 스폰 지점)이며, 스테이지 전환 시점에 플레이어가 이미 다른
    곳에 있다면 그 위치도 같이 넘겨서 "장애물이 새로 생기며 플레이어 위에
    겹쳐버리는" 상황을 방지합니다."""
    if count is None:
        # 스테이지가 올라갈수록 장애물을 조금씩 더 배치해서 맵이 점점
        # 복잡해지는 느낌을 줍니다(너무 빽빽해지지 않도록 상한을 둠).
        count = min(9, 5 + stage)

    obstacles = []

    world_w, world_h = config.WORLD_WIDTH, config.WORLD_HEIGHT
    center_x, center_y = world_w / 2, world_h / 2

    if protect_points is None:
        protect_points = [(center_x, center_y)]

    # 스폰 안전지대: 보호 지점(맵 중앙 및/또는 현재 플레이어 위치) 주변에는
    # 장애물을 두지 않음.
    safe_radius = 260 * config.UI_SCALE

    min_size = round(70 * config.UI_SCALE)
    max_size = round(160 * config.UI_SCALE)
    min_gap = round(40 * config.UI_SCALE)   # 장애물끼리 최소 간격
    edge_margin = round(80 * config.UI_SCALE)  # 월드 가장자리에는 배치하지 않음

    max_attempts_per_obstacle = 40

    for _ in range(count):
        for _attempt in range(max_attempts_per_obstacle):
            w = random.randint(min_size, max_size)
            h = random.randint(min_size, max_size)
            x = random.randint(edge_margin, max(edge_margin, world_w - edge_margin - w))
            y = random.randint(edge_margin, max(edge_margin, world_h - edge_margin - h))

            cand_cx, cand_cy = x + w / 2, y + h / 2

            # 규칙 1: 보호 지점(들)과 겹치지 않기
            too_near_protected = any(
                ((cand_cx - px) ** 2 + (cand_cy - py) ** 2) ** 0.5 < safe_radius + max(w, h) / 2
                for px, py in protect_points
            )
            if too_near_protected:
                continue

            # 규칙 2: 기존 장애물들과 최소 간격 유지
            too_close = False
            for other in obstacles:
                if (other.rect.inflate(min_gap * 2, min_gap * 2)).colliderect(
                    (x - min_gap, y - min_gap, w + min_gap * 2, h + min_gap * 2)
                ):
                    too_close = True
                    break
            if too_close:
                continue

            obstacles.append(Obstacle(x, y, w, h))
            break
        # max_attempts를 다 써도 자리를 못 찾으면 이번 장애물은 그냥 건너뜁니다
        # (맵이 이미 충분히 채워졌다는 뜻이라 억지로 욱여넣지 않습니다).

    return obstacles
