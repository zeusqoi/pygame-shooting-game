# utils/flowfield.py
"""
좀비들이 장애물을 자연스럽게 피해서 플레이어에게 다가오도록 하는 "플로우 필드"
경로탐색입니다.

기존에는 좀비가 매 프레임 "플레이어 방향 벡터"로 직진만 해서, 장애물이 생기면
그대로 파묻히거나 뚫고 지나가야 했습니다. 플로우 필드는 다음처럼 동작합니다:

1. 월드를 일정 크기(cell_size)의 격자로 나눈다.
2. 장애물과 겹치는 칸은 "막힘"으로 표시한다.
3. 살아있는 모든 플레이어 위치를 "출발점"으로 삼아 다익스트라(가중치 있는
   BFS)를 한 번 돌려서, 모든 칸에 대해 "가장 가까운 플레이어까지의 최단 비용"을
   계산한다(= integration field).
4. 각 칸에서 비용이 더 낮은 이웃 칸 방향을 그 칸의 "흐름 방향"으로 저장한다
   (= flow field). 대각선 이웃도 포함해서 8방향으로 부드럽게 움직입니다.

좀비는 매 프레임 자기가 있는 칸의 흐름 방향을 그냥 조회해서 그 방향으로
이동합니다. 격자 전체는 GameScene에서 주기적으로(매 프레임이 아니라 일정
간격으로) 다시 계산해서 모든 좀비가 공유합니다 - 좀비 수가 몇 마리든 매
프레임 각자 경로를 다시 계산하지 않아도 되므로 좀비가 많아져도 가볍습니다.
"""

import heapq
import math

import config


class FlowField:
    _NEIGHBORS = [
        (-1, -1, math.sqrt(2)), (0, -1, 1.0), (1, -1, math.sqrt(2)),
        (-1, 0, 1.0),                          (1, 0, 1.0),
        (-1, 1, math.sqrt(2)), (0, 1, 1.0), (1, 1, math.sqrt(2)),
    ]

    def __init__(self, obstacles):
        # 셀 크기도 다른 게임 내 거리값들처럼 UI_SCALE에 맞춰 스케일링해서,
        # 화면 크기가 달라져도 격자 해상도(칸 개수)가 항상 비슷하게 유지되도록 합니다.
        self.cell_size = max(16, round(64 * config.UI_SCALE))
        self.cols = max(1, math.ceil(config.WORLD_WIDTH / self.cell_size))
        self.rows = max(1, math.ceil(config.WORLD_HEIGHT / self.cell_size))
        self.blocked = self._build_blocked_grid(obstacles)
        self.cost = None
        self.dirs = {}

    def _build_blocked_grid(self, obstacles):
        blocked = [[False] * self.cols for _ in range(self.rows)]
        for obs in obstacles:
            r = obs.hitbox
            c0 = max(0, r.left // self.cell_size)
            c1 = min(self.cols - 1, r.right // self.cell_size)
            row0 = max(0, r.top // self.cell_size)
            row1 = min(self.rows - 1, r.bottom // self.cell_size)
            for row in range(int(row0), int(row1) + 1):
                for col in range(int(c0), int(c1) + 1):
                    blocked[row][col] = True
        return blocked

    def world_to_cell(self, pos):
        col = int(pos[0] // self.cell_size)
        row = int(pos[1] // self.cell_size)
        col = max(0, min(self.cols - 1, col))
        row = max(0, min(self.rows - 1, row))
        return col, row

    def is_blocked_cell(self, col, row):
        return self.blocked[row][col]

    def recompute(self, goal_positions):
        """goal_positions: 살아있는 플레이어들의 (x, y) 월드 좌표 리스트."""
        INF = float("inf")
        cost = [[INF] * self.cols for _ in range(self.rows)]
        heap = []

        for gx, gy in goal_positions:
            gc, gr = self.world_to_cell((gx, gy))
            if not self.blocked[gr][gc] and cost[gr][gc] > 0:
                cost[gr][gc] = 0.0
                heapq.heappush(heap, (0.0, gc, gr))

        while heap:
            d, c, r = heapq.heappop(heap)
            if d > cost[r][c]:
                continue
            for dc, dr, step in self._NEIGHBORS:
                nc, nr = c + dc, r + dr
                if 0 <= nc < self.cols and 0 <= nr < self.rows and not self.blocked[nr][nc]:
                    nd = d + step
                    if nd < cost[nr][nc]:
                        cost[nr][nc] = nd
                        heapq.heappush(heap, (nd, nc, nr))

        self.cost = cost

        dirs = {}
        for r in range(self.rows):
            row_cost = cost[r]
            for c in range(self.cols):
                if self.blocked[r][c] or row_cost[c] == INF:
                    continue
                best_cost = row_cost[c]
                best_dir = None
                for dc, dr, _step in self._NEIGHBORS:
                    nc, nr = c + dc, r + dr
                    if 0 <= nc < self.cols and 0 <= nr < self.rows and cost[nr][nc] < best_cost:
                        best_cost = cost[nr][nc]
                        best_dir = (dc, dr)
                if best_dir is not None:
                    mag = math.hypot(best_dir[0], best_dir[1])
                    dirs[(c, r)] = (best_dir[0] / mag, best_dir[1] / mag)
        self.dirs = dirs

    def get_direction(self, pos):
        """이 위치에서 플레이어 쪽으로 가는 흐름 방향(정규화된 (dx, dy))을
        반환합니다. 경로가 없거나 아직 계산 전이면 None."""
        cell = self.world_to_cell(pos)
        return self.dirs.get(cell)
