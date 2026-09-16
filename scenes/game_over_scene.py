import pygame
import pygame_gui
import config
from core.globals import main_bg_img, gameover_img
from core.scene_manager import Scene
from utils.ui_utils import draw_bg_aspect_ratio

class GameOverScene(Scene):
    def __init__(self, kills, cleared=False):
        super().__init__()
        self.kills = kills
        self.cleared = cleared

        self.ui_manager = pygame_gui.UIManager(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT), None
        )
        self.btn_menu = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((440, 580), (400, 70)),
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

            clear_font = pygame.font.Font(None, 100)
            txt = clear_font.render("STAGE CLEAR!", True, (255, 220, 0))
            screen.blit(txt, (config.SCREEN_WIDTH // 2 - txt.get_width() // 2, 200))

            kill_font = pygame.font.Font(None, 60)
            kill_txt = kill_font.render(f"Kills: {self.kills}", True, config.WHITE)
            screen.blit(kill_txt, (config.SCREEN_WIDTH // 2 - kill_txt.get_width() // 2, 340))
        else:
            if gameover_img:
                scaled = pygame.transform.scale(gameover_img, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
                screen.blit(scaled, (0, 0))
            else:
                screen.fill(config.BLACK)
                over_font = pygame.font.Font(None, 120)
                txt = over_font.render("GAME OVER", True, config.RED)
                screen.blit(txt, (config.SCREEN_WIDTH // 2 - txt.get_width() // 2, 220))

            kill_font = pygame.font.Font(None, 60)
            kill_txt = kill_font.render(f"Kills: {self.kills}", True, config.WHITE)
            screen.blit(kill_txt, (config.SCREEN_WIDTH // 2 - kill_txt.get_width() // 2, 500))

        self.ui_manager.draw_ui(screen)