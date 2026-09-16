import pygame
import pygame_gui
import config
from core.globals import theme_path, db, main_bg_img
from core.scene_manager import Scene
from utils.ui_utils import draw_bg_aspect_ratio

class SignupSubScene(Scene):
    def __init__(self):
        super().__init__()
        self.ui_manager = pygame_gui.UIManager((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), theme_path)

        # 1. 중앙 패널 (로그인 화면과 통일감 있는 컴팩트한 사이즈)
        panel_rect = pygame.Rect((340, 100), (600, 620))
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=panel_rect,
            manager=self.ui_manager,
            object_id="@login_panel"
        )

        # 2. 타이틀 (디자인 아이디 적용)
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 40), (600, 60)),
            text="JOIN FORCES",
            manager=self.ui_manager,
            container=self.panel,
            object_id="@login_title"
        )

        # --- ID 영역 (Placeholder 적용) ---
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 120), (300, 30)),
            text="ID *", manager=self.ui_manager, container=self.panel, object_id="@login_label"
        )
        self.id_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((50, 150), (380, 60)),
            manager=self.ui_manager, 
            container=self.panel, 
            object_id="@login_input",
            placeholder_text="ENTER YOUR ID" # 초기 값 제거 및 Placeholder 적용
        )

        self.btn_check_id = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((440, 150), (110, 60)),
            text="CHECK", manager=self.ui_manager, container=self.panel, object_id="@login_check_btn"
        )

        # --- 비밀번호 영역 (Placeholder 적용) ---
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 240), (240, 30)),
            text="PASSWORD *", manager=self.ui_manager, container=self.panel, object_id="@login_label"
        )
        self.pw_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((50, 270), (240, 60)),
            manager=self.ui_manager, 
            container=self.panel, 
            object_id="@login_input",
            placeholder_text="PASSWORD"
        )
        self.pw_entry.set_text_hidden(True) 

        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((310, 240), (240, 30)),
            text="CONFIRM PASSWORD *", manager=self.ui_manager, container=self.panel, object_id="@login_label"
        )
        self.pw_confirm_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((310, 270), (240, 60)),
            manager=self.ui_manager, 
            container=self.panel, 
            object_id="@login_input",
            placeholder_text="CONFIRM PASSWORD"
        )
        self.pw_confirm_entry.set_text_hidden(True) 

        # --- 닉네임/이메일 영역 (Placeholder 적용) ---
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((50, 360), (240, 30)),
            text="NICKNAME *", manager=self.ui_manager, container=self.panel, object_id="@login_label"
        )
        self.nickname_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((50, 390), (240, 60)),
            manager=self.ui_manager, 
            container=self.panel, 
            object_id="@login_input",
            placeholder_text="DISPLAY NAME"
        )

        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((310, 360), (240, 30)),
            text="EMAIL (OPTIONAL)", manager=self.ui_manager, container=self.panel, object_id="@login_label"
        )
        self.email_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((310, 390), (240, 60)),
            manager=self.ui_manager, 
            container=self.panel, 
            object_id="@login_input",
            placeholder_text="RECOVERY EMAIL"
        )

        # --- 하단 버튼부 ---
        self.btn_cancel = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((50, 500), (150, 60)),
            text="CANCEL", manager=self.ui_manager, container=self.panel, object_id="@login_cancel_btn"
        )

        self.btn_submit = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((210, 500), (340, 60)),
            text="COMPLETE SIGNUP", manager=self.ui_manager, container=self.panel, object_id="@login_submit_btn"
        )

        # 메시지 라벨
        self.msg_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((0, 570), (600, 30)),
            text="", manager=self.ui_manager, container=self.panel, object_id="@login_msg"
        )

        self.id_verified = False

    def handle_events(self, events):
        from scenes.title_scene import TitleScene

        for e in events:
            self.ui_manager.process_events(e)
            if e.type == pygame_gui.UI_BUTTON_PRESSED:
                if e.ui_element == self.btn_check_id:
                    username = self.id_entry.get_text()
                    if not username: # Placeholder를 사용하므로 빈 값 체크로 변경
                        self.msg_label.set_text("PLEASE ENTER ID")
                    elif db.check_id_duplicate(username):
                        self.msg_label.set_text("ID ALREADY EXISTS")
                        self.id_verified = False
                    else:
                        self.msg_label.set_text("ID IS AVAILABLE")
                        self.id_verified = True

                elif e.ui_element == self.btn_submit:
                    self.process_signup()

                elif e.ui_element == self.btn_cancel:
                    self.manager.switch_to(TitleScene())

    def process_signup(self):
        username = self.id_entry.get_text()
        pw = self.pw_entry.get_text()
        pw_confirm = self.pw_confirm_entry.get_text()
        nickname = self.nickname_entry.get_text()
        email = self.email_entry.get_text()

        if not self.id_verified:
            self.msg_label.set_text("PLEASE CHECK ID DUPLICATE FIRST")
            return
        if not pw or pw != pw_confirm:
            self.msg_label.set_text("PASSWORDS DO NOT MATCH")
            return
        if not nickname:
            self.msg_label.set_text("PLEASE ENTER NICKNAME")
            return

        if db.register(username, pw, nickname, email if email else None):
            self.msg_label.set_text("SIGNUP COMPLETE! GO TO LOGIN")
        else:
            self.msg_label.set_text("SIGNUP FAILED")

    def update(self, time_delta):
        self.ui_manager.update(time_delta)

    def draw(self, screen):
        if main_bg_img:
            draw_bg_aspect_ratio(screen, main_bg_img)
        else:
            screen.fill(config.BLACK)
        self.ui_manager.draw_ui(screen)
