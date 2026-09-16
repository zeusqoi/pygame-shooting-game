import pygame
import pygame_gui
import config
from core.globals import main_bg_img
from core.scene_manager import Scene
from utils.ui_utils import draw_bg_aspect_ratio, generate_gradient_surface
from utils.layout import scaled_rect, scaled_size

class GameOverScene(Scene):
    def __init__(self, kills, cleared=False):
        super().__init__()
        self.kills = kills
        self.cleared = cleared

        # 게임오버 화면은 기존의 복잡한 합성 사진(GAMEOVER.png) 대신,
        # 다른 화면들과 톤을 맞춘 붉은 계열 그라데이션 배경을 사용합니다.
        # (매 프레임 새로 만들지 않도록 여기서 한 번만 생성해둡니다.)
        self.gameover_bg = generate_gradient_surface(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), (60, 12, 14), (12, 4, 6)
        )

        self.ui_manager = pygame_gui.UIManager(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), None
        )
        self.btn_menu = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(440, 580, 400, 70),
            text="Back to Menu",
            manager=self.ui_manager,
            object_id="@login_back_btn"
        )

    def handle_events(self, events):
        for e in events:
            self.ui_manager.process_events(e)
            if e.type == pygame_gui.UI_BUTTON_PRESSED:
                if e.ui_element == self.btn_menu:
                    from scenes.title_scene import TitleScene
                    self.manager.switch_to(TitleScene())

    def update(self, time_delta):
        self.ui_manager.update(time_delta)

    def draw(self, screen):
        if self.cleared:
            if main_bg_img:
                draw_bg_aspect_ratio(screen, main_bg_img)
            else:
                screen.fill(config.BLACK)

            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            clear_font = pygame.font.Font(None, scaled_size(100))
            txt = clear_font.render("STAGE CLEAR!", True, (255, 220, 0))
            screen.blit(txt, (config.SCREEN_WIDTH // 2 - txt.get_width() // 2, scaled_size(200)))

            kill_font = pygame.font.Font(None, scaled_size(60))
            kill_txt = kill_font.render(f"Kills: {self.kills}", True, config.WHITE)
            screen.blit(kill_txt, (config.SCREEN_WIDTH // 2 - kill_txt.get_width() // 2, scaled_size(340)))
        else:
            screen.blit(self.gameover_bg, (0, 0))

            over_font = pygame.font.Font(None, scaled_size(130))
            txt = over_font.render("GAME OVER", True, (235, 70, 70))
            screen.blit(txt, (config.SCREEN_WIDTH // 2 - txt.get_width() // 2, scaled_size(190)))

            kill_font = pygame.font.Font(None, scaled_size(56))
            kill_txt = kill_font.render(f"Kills: {self.kills}", True, config.WHITE)
            screen.blit(kill_txt, (config.SCREEN_WIDTH // 2 - kill_txt.get_width() // 2, scaled_size(460)))

        self.ui_manager.draw_ui(screen)