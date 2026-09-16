import pygame
import pygame_gui
import config
from core.globals import theme_path, current_user, main_bg_img
from core.scene_manager import Scene
from utils.ui_utils import draw_bg_aspect_ratio
from utils.sound_manager import play_music, set_bgm_volume, set_sfx_volume, get_bgm_volume, get_sfx_volume
from utils.layout import scaled_rect


class SettingsPopup:
    """BGM / 효과음 볼륨을 조절하는 설정 팝업."""

    def __init__(self, manager):
        self.manager = manager

        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=scaled_rect(390, 260, 500, 300),
            manager=manager,
            object_id="#login_popup"
        )

        self.title = pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(0, 10, 500, 40),
            text="SETTINGS",
            manager=manager,
            container=self.panel,
            object_id="#popup_title"
        )

        self.bgm_label = pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(30, 70, 200, 30),
            text="BGM Volume",
            manager=manager,
            container=self.panel,
            object_id="#popup_text"
        )
        self.bgm_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=scaled_rect(30, 105, 440, 30),
            start_value=get_bgm_volume() * 100,
            value_range=(0, 100),
            manager=manager,
            container=self.panel
        )

        self.sfx_label = pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(30, 150, 200, 30),
            text="SFX Volume",
            manager=manager,
            container=self.panel,
            object_id="#popup_text"
        )
        self.sfx_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=scaled_rect(30, 185, 440, 30),
            start_value=get_sfx_volume() * 100,
            value_range=(0, 100),
            manager=manager,
            container=self.panel
        )

        self.btn_close = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(175, 235, 150, 40),
            text="CLOSE",
            manager=manager,
            container=self.panel,
            object_id="#popup_ok"
        )

    def handle_slider_event(self, event):
        if event.ui_element == self.bgm_slider:
            set_bgm_volume(self.bgm_slider.get_current_value() / 100)
        elif event.ui_element == self.sfx_slider:
            set_sfx_volume(self.sfx_slider.get_current_value() / 100)

    def kill(self):
        self.panel.kill()


class LoginWarningPopup:
    def __init__(self, manager):
        self.manager = manager

        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=scaled_rect(390, 300, 500, 220),
            manager=manager,
            object_id="#login_popup"
        )

        self.title = pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(0, 10, 500, 40),
            text="WARNING",
            manager=manager,
            container=self.panel,
            object_id="#popup_title"
        )

        self.text = pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(20, 70, 460, 60),
            text="Your score will not be saved",
            manager=manager,
            container=self.panel,
            object_id="#popup_text"
        )

        self.sub_text = pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(20, 105, 460, 40),
            text="if you play as Guest.",
            manager=manager,
            container=self.panel,
            object_id="#popup_text"
        )

        self.btn_cancel = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(60, 155, 150, 40),
            text="CANCEL",
            manager=manager,
            container=self.panel,
            object_id="#popup_cancel"
        )

        self.btn_ok = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(290, 155, 150, 40),
            text="OK",
            manager=manager,
            container=self.panel,
            object_id="#popup_ok"
        )

    def kill(self):
        self.panel.kill()


class TitleScene(Scene):
    def __init__(self):
        super().__init__()
        self.ui_manager = pygame_gui.UIManager((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), theme_path)

        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(40, 60, 1200, 250),
            text="TRAIN TO MAGOK",
            manager=self.ui_manager,
            object_id="#title_text"
        )
        import core.globals as globals
        if globals.current_user != "Guest":
            self.subtitle_label = pygame_gui.elements.UILabel(
                relative_rect=scaled_rect(440, 300, 400, 60),
                text=globals.current_user,
                manager=self.ui_manager,
                object_id="#subtitle_text"
            )
        else:
            self.subtitle_label = None

        self.btn_start = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(390, 420, 500, 70),
            text="GAME START",
            manager=self.ui_manager,
            object_id="@green_btn"
        )
        self.btn_login = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(390, 510, 240, 50),
            text="LOGIN",
            manager=self.ui_manager,
            object_id="@dark_btn"
        )
        self.btn_signup = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(650, 510, 240, 50),
            text="SIGN UP",
            manager=self.ui_manager,
            object_id="@dark_btn"
        )
        self.btn_ranking = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(390, 580, 500, 50),
            text="RANKING",
            manager=self.ui_manager,
            object_id="@dark_btn"
        )
        self.btn_settings = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(390, 640, 500, 50),
            text="SETTINGS",
            manager=self.ui_manager,
            object_id="@dark_btn"
        )

        self.message_window = None
        self.login_popup = None
        self.settings_popup = None

        # 타이틀/메뉴 배경음
        try:
            play_music(config.SOUND_TITLE_BGM, volume=0.5)
        except Exception as e:
            print("타이틀 배경음 실행 실패:", e)

    def handle_events(self, events):
        from scenes.character_select_scene import CharacterSelectScene
        from scenes.login_scene import LoginSubScene
        from scenes.signup_scene import SignupSubScene
        from scenes.ranking_scene import RankingScene
        import core.globals as globals

        for e in events:
            self.ui_manager.process_events(e)

            if e.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                if self.settings_popup:
                    self.settings_popup.handle_slider_event(e)

            if e.type == pygame_gui.UI_BUTTON_PRESSED:
                if self.settings_popup:
                    if e.ui_element == self.settings_popup.btn_close:
                        self.settings_popup.kill()
                        self.settings_popup = None
                    continue

                if self.login_popup:
                    if e.ui_element == self.login_popup.btn_cancel:
                        self.login_popup.kill()
                        self.login_popup = None

                    elif e.ui_element == self.login_popup.btn_ok:
                        self.login_popup.kill()
                        self.login_popup = None
                        globals.set_current_user("Guest")
                        self.manager.switch_to(CharacterSelectScene())

                elif e.ui_element == self.btn_start:
                    if globals.current_user == "Guest":
                        self.login_popup = LoginWarningPopup(self.ui_manager)
                    else:
                        self.manager.switch_to(CharacterSelectScene())

                elif e.ui_element == self.btn_login:
                    self.manager.switch_to(LoginSubScene())

                elif e.ui_element == self.btn_signup:
                    self.manager.switch_to(SignupSubScene())

                elif e.ui_element == self.btn_ranking:
                    self.manager.switch_to(RankingScene(back_scene_class=TitleScene))

                elif e.ui_element == self.btn_settings:
                    self.settings_popup = SettingsPopup(self.ui_manager)

    def update(self, time_delta):
        self.ui_manager.update(time_delta)

    def draw(self, screen):
        if main_bg_img:
            draw_bg_aspect_ratio(screen, main_bg_img)
        else:
            screen.fill(config.BLACK)
        self.ui_manager.draw_ui(screen)