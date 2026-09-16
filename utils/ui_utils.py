import pygame

def draw_bg_aspect_ratio(surface, bg_image):
    """빈 공간 없이 화면 크기에 딱 맞게 꽉 채우도록 배경을 그립니다."""
    if bg_image is None:
        return
    screen_rect = surface.get_rect()
    scaled_img = pygame.transform.scale(bg_image, (screen_rect.width, screen_rect.height))
    surface.blit(scaled_img, (0, 0))
