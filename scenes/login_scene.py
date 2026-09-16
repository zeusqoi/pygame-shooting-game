import pygame
import pygame_gui
import config
from core.globals import theme_path, db, main_bg_img
import core.globals as globals
from core.scene_manager import Scene
from utils.ui_utils import draw_bg_aspect_ratio
from utils.sound_manager import play_sound
from utils.layout import scaled_rect


class LoginSubScene(Scene):
    def __init__(self):
        super().__init__()
        self.ui_manager = pygame_gui.UIManager(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
            theme_path
        )

        panel_rect = scaled_rect(390, 75, 500, 650)
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=panel_rect,
            manager=self.ui_manager,
            object_id="@login_panel"
        )

        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(44, 40, 412, 60),
            text="Login",
            manager=self.ui_manager,
            container=self.panel,
            object_id="@login_title"
        )

        self.id_label = pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(44, 150, 412, 30),
            text="ID",
            manager=self.ui_manager,
            container=self.panel,
            object_id="@input_label"
        )

        self.id_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=scaled_rect(44, 180, 412, 60),
            manager=self.ui_manager,
            container=self.panel,
            placeholder_text="ENTER YOUR ID",
            object_id="@login_input"
        )

        self.pw_label = pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(44, 280, 412, 30),
            text="PASSWORD",
            manager=self.ui_manager,
            container=self.panel,
            object_id="@input_label"
        )

        self.pw_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=scaled_rect(44, 310, 412, 60),
            manager=self.ui_manager,
            container=self.panel,
            placeholder_text="ENTER PASSWORD",
            object_id="@login_input"
        )
        self.pw_entry.set_text_hidden(True)

        self.btn_submit = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(44, 440, 412, 60),
            text="Login",
            manager=self.ui_manager,
            container=self.panel,
            object_id="@login_submit_btn"
        )

        self.btn_back = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(44, 530, 412, 60),
            text="Back to Menu",
            manager=self.ui_manager,
            container=self.panel,
            object_id="@login_back_btn"
        )

        self.msg_label = pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(44, 580, 412, 30),
            text="",
            manager=self.ui_manager,
            container=self.panel,
            object_id="@input_label"
        )

    def handle_events(self, events):
        from scenes.title_scene import TitleScene
        from scenes.character_select_scene import CharacterSelectScene

        for e in events:
            self.ui_manager.process_events(e)

            should_login = False

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    should_login = True

            if e.type == pygame_gui.UI_BUTTON_PRESSED:
                if e.ui_element == self.btn_submit:
                    should_login = True

            if should_login:
                curr_id = self.id_entry.get_text()
                curr_pw = self.pw_entry.get_text()

                if not curr_id or curr_id == "ENTER YOUR ID" or not curr_pw:
                    self.msg_label.set_text("Please enter ID and PW")
                else:
                    if db.conn is None:
                        if curr_id == "admin" and curr_pw == "1234":
                            globals.set_current_user(curr_id)
                            self.manager.switch_to(CharacterSelectScene())
                        else:
                            self.msg_label.set_text("Offline: Use admin / 1234")
                            play_sound("로그인 실패 시 효과음.mp3", volume=0.5)
                    else:
                        if db.login(curr_id, curr_pw):
                            globals.set_current_user(curr_id)
                            self.manager.switch_to(CharacterSelectScene())
                        else:
                            self.msg_label.set_text("Login Failed")
                            play_sound("로그인 실패 시 효과음.mp3", volume=0.5)

            if e.type == pygame_gui.UI_BUTTON_PRESSED:
                if e.ui_element == self.btn_back:
                    self.manager.switch_to(TitleScene())

            if e.type == pygame.USEREVENT:
                user_event_type = getattr(e, 'user_type', None)
                if user_event_type is not None:
                    if "text_entry_focused" in str(user_event_type).lower():
                        if e.ui_element == self.id_entry:
                            self.id_entry.set_text("")
                        elif e.ui_element == self.pw_entry:
                            self.pw_entry.set_text("")

    def update(self, time_delta):
        self.ui_manager.update(time_delta)

    def draw(self, screen):
        if main_bg_img:
            draw_bg_aspect_ratio(screen, main_bg_img)
        else:
            screen.fill(config.BLACK)
        self.ui_manager.draw_ui(screen)