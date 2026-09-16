import pygame


def generate_gradient_surface(size, top_color, bottom_color):
    """위에서 아래로 부드럽게 색이 변하는 단색 그라데이션 배경을 만듭니다.

    화려한 사진 배경 대신 간결한 배경이 필요할 때 사용합니다. 실행 시 한 번만
    생성해서 재사용하면 되고(매 프레임 새로 만들 필요 없음), 나중에 실제 배경
    이미지 파일이 준비되면 이 함수 호출 대신 pygame.image.load(경로)로
    교체하기만 하면 됩니다.
    """
    width, height = size
    try:
        surf = pygame.Surface(size).convert()
    except pygame.error:
        # 디스플레이가 아직 초기화되지 않은 경우를 대비한 안전장치
        surf = pygame.Surface(size)
    height = max(height, 1)
    for y in range(height):
        t = y / max(height - 1, 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (width, y))
    return surf


def draw_bg_aspect_ratio(surface, bg_image):
    """빈 공간 없이 화면 크기에 딱 맞게 꽉 채우도록 배경을 그립니다."""
    if bg_image is None:
        return
    screen_rect = surface.get_rect()
    scaled_img = pygame.transform.scale(bg_image, (screen_rect.width, screen_rect.height))
    surface.blit(scaled_img, (0, 0))
