# character_select_scene.py

import pygame
import pygame_gui
import os
import config
from core.globals import theme_path, CHAR_DATA, main_bg_img
from core.scene_manager import Scene
from utils.ui_utils import draw_bg_aspect_ratio
from scenes.intro_scene import IntroScene
from utils.layout import scaled_rect

# 캐릭터별 패시브 / 공통 2차 능력 / 2인 협동 기술 설명.
# 실제 수치는 models/player.py, scenes/game_scene.py의 값과 맞춰뒀습니다.
PASSIVE_DESC = {
    "choi": "패시브: 연속 공격 시 대미지 증가 (최대 +25%)",
    "ma": "패시브: 체력이 낮을수록 받는 피해 감소 (최대 -50%)",
    "gong": "패시브: 가만히 서 있을수록 대미지 증가 (최대 +45%)",
}
DASH_DESC = "회피 대시: 짧은 무적으로 위기 탈출 (쿨타임 3초, 1P:LShift / 2P:RCtrl)"
COMBO_DESC = "2인 협동: 서로 가까이 붙어 스킬을 거의 동시에 쓰면 강력한 연계 공격 발동! (쿨타임 15초)"

# 캐릭터 카드 안에 바로 보이는 짧은 패시브 태그(선택 전에도 항상 표시).
PASSIVE_SHORT = {
    "choi": "패시브: 콤보 대미지↑",
    "ma": "패시브: 피해 감소↑",
    "gong": "패시브: 조준 강화↑",
}


class CharacterSelectScene(Scene):
    def __init__(self, players=1):
        super().__init__()
        self.ui_manager = pygame_gui.UIManager((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), theme_path)
        self.players = players
        self.p1_selection = None
        self.p2_selection = None
        
        # 1. Top Bar
        self.setup_label = pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(40, 30, 300, 80),
            text="SETUP",
            manager=self.ui_manager,
            object_id="#menu_title"
        )
        self.btn_back = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(1100, 30, 140, 40),
            text="BACK",
            manager=self.ui_manager,
            object_id="@tab_inactive"
        )
        
        # 2. Select Mode Section
        # 기존 150px에서 130px로 줄여서, 그만큼 아래 설명 박스가 스크롤 없이
        # 내용을 보여줄 수 있도록 세로 공간을 더 확보합니다.
        self.mode_panel = pygame_gui.elements.UIPanel(
            relative_rect=scaled_rect(40, 110, 1200, 130),
            manager=self.ui_manager,
            object_id="@rank_normal_panel"
        )
        pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(20, 10, 300, 40),
            text="SELECT MODE",
            manager=self.ui_manager,
            container=self.mode_panel,
            object_id="#ranking_header_text"
        )
        self.btn_1p = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(20, 50, 400, 60),
            text="1 PLAYER",
            manager=self.ui_manager,
            container=self.mode_panel,
            object_id="@tab_active" if self.players == 1 else "@tab_inactive"
        )
        self.btn_2p = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(440, 50, 400, 60),
            text="2 PLAYERS",
            manager=self.ui_manager,
            container=self.mode_panel,
            object_id="@tab_active" if self.players == 2 else "@tab_inactive"
        )

        # 3. Select Character Section
        # 위 mode_panel을 줄이고, 아래 START GAME 버튼도 더 내려서 확보한
        # 여유 공간만큼 char_panel을 키워 설명 박스에 스크롤 없이 내용이
        # 다 들어가도록 합니다.
        self.char_panel = pygame_gui.elements.UIPanel(
            relative_rect=scaled_rect(40, 245, 1200, 465),
            manager=self.ui_manager,
            object_id="@rank_normal_panel"
        )
        pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(20, 10, 400, 40),
            text="SELECT CHARACTER",
            manager=self.ui_manager,
            container=self.char_panel,
            object_id="#ranking_header_text"
        )
        # 카드 자체가 선택되면 초록 테두리로 강조되기 때문에, 상단에 별도로
        # "P1: Dongseok" 같은 텍스트 배지를 또 보여줄 필요가 없다는 피드백에
        # 따라 화면에서 뺐습니다. _update_selection_label()이 내부적으로
        # 텍스트/스타일을 계속 갱신하긴 하지만, 라벨 자체를 숨겨서 화면에는
        # 나타나지 않습니다.
        self.selection_label = pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(780, 10, 400, 40),
            text="P1: NONE",
            manager=self.ui_manager,
            container=self.char_panel,
            object_id="#badge_1p"
        )
        self.selection_label.hide()
        
        # Character Slots
        self.char_slots = []
        self.char_images = []
        slot_width = 240
        # 카드 안에 이미지+이름+패시브 태그를 다 담으면서도, 아래쪽 설명
        # 박스(desc_box)가 스크롤 없이 내용을 보여줄 수 있도록 높이를
        # 190px로 잡았습니다.
        slot_height = 190
        num_chars = len(CHAR_DATA)
        total_slots_width = num_chars * slot_width
        spacing = (1200 - total_slots_width) // (num_chars + 1)
        x_offset = spacing
        y_offset = 50
        
        for char_id, data in CHAR_DATA.items():
            # Use UIPanel as the container for the slot
            slot_container = pygame_gui.elements.UIPanel(
                relative_rect=scaled_rect(x_offset, y_offset, slot_width, slot_height),
                manager=self.ui_manager,
                container=self.char_panel,
                object_id="@rank_normal_panel"
            )
            
            # Transparent Button on top for clicks
            slot_btn = pygame_gui.elements.UIButton(
                relative_rect=scaled_rect(0, 0, slot_width, slot_height),
                text="",
                manager=self.ui_manager,
                container=slot_container,
                object_id="@transparent_btn" # We should define this or use a style that has no bg
            )
            
            # Image
            # 카드 안에 패시브 태그를 한 줄 더 넣을 자리를 만들기 위해
            # 기존 120x120에서 110x110으로 살짝 줄였습니다.
            char_prefix = data["name"].lower()
            img_path = f"assets/images/{char_prefix}_default.png"
            if os.path.exists(img_path):
                try:
                    img_surf = pygame.image.load(img_path).convert_alpha()
                    img_surf = pygame.transform.scale(img_surf, (110, 110))
                    self.char_images.append(img_surf)
                    pygame_gui.elements.UIImage(
                        relative_rect=scaled_rect(65, 15, 110, 110),
                        image_surface=img_surf,
                        manager=self.ui_manager,
                        container=slot_container
                    )
                except Exception as e:
                    print(f"Failed to load {img_path}: {e}")

            # Name Label
            # 카드 안 패시브 태그(알약 배지)는 위쪽 P1/P2 배지와 마찬가지로
            # 뺐습니다(설명 박스에 이미 패시브 정보가 나오기 때문). 그만큼
            # 남는 공간에서 이름이 더 가운데 오도록 위치를 살짝 내렸습니다.
            pygame_gui.elements.UILabel(
                relative_rect=scaled_rect(0, 140, slot_width, 34),
                text=data["name"],
                manager=self.ui_manager,
                container=slot_container,
                object_id="#rank_normal_text"
            )

            self.char_slots.append((slot_btn, slot_container, char_id))
            x_offset += slot_width + spacing
            
        # Description Box
        # 캐릭터 한 명만 골랐을 때는 그 캐릭터 설명만, 2인 모드에서 둘 다 골랐을
        # 때는 두 캐릭터 설명 + 공통 대시 + 2인 협동 기술 설명까지 같이 보여주기
        # 위해 기존 80px보다 넉넉하게 높이를 잡았습니다.
        # 아무도 선택하지 않은 상태에서는 아예 숨겨뒀다가, 캐릭터를 고르는 순간
        # 처음 나타나도록 해서 그 등장 자체가 눈에 띄게 만듭니다.
        self.desc_box = pygame_gui.elements.UITextBox(
            relative_rect=scaled_rect(20, 248, 1160, 180),
            html_text="",
            manager=self.ui_manager,
            container=self.char_panel,
            object_id="#char_desc_text"
        )
        self.desc_box.hide()
            
        # 4. Start Game Button
        self.btn_start = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(440, 715, 400, 65),
            text="START GAME",
            manager=self.ui_manager,
            object_id="@green_btn"
        )
        self.message_window = None

        # 캐릭터를 고를 때마다 그 카드 주위로 잠깐 퍼져나가며 사라지는
        # 링(pulse) 효과를 줘서, 방금 무엇을 선택했는지 시선이 가도록 합니다.
        self.anim_char_id = None
        self.anim_desc_pulse = False
        self.anim_timer = 0.0
        self.anim_duration = 0.35

    def handle_events(self, events):
        from scenes.game_scene import GameScene
        from scenes.title_scene import TitleScene
        from scenes.intro_scene import IntroScene

        for e in events:
            self.ui_manager.process_events(e)
            if e.type == pygame_gui.UI_BUTTON_PRESSED:
                if e.ui_element == self.btn_back:
                    self.manager.switch_to(TitleScene())
                elif e.ui_element == self.btn_1p:
                    self.players = 1
                    self.p2_selection = None
                    self.btn_1p.change_object_id("@tab_active")
                    self.btn_2p.change_object_id("@tab_inactive")
                    self._update_selection_label()
                    self._update_slot_highlights()
                    self._refresh_description()
                elif e.ui_element == self.btn_2p:
                    self.players = 2
                    self.btn_1p.change_object_id("@tab_inactive")
                    self.btn_2p.change_object_id("@tab_active")
                    self._update_selection_label()
                    self._update_slot_highlights()
                    self._refresh_description()
                elif e.ui_element == self.btn_start:
                    if self.players == 1 and not self.p1_selection:
                        self._show_warning("Please select a character for P1.")
                    elif self.players == 2 and (not self.p1_selection or not self.p2_selection):
                        self._show_warning("Both players must select characters.")
                    else:
                        p2_char = self.p2_selection if self.players == 2 else None
                        self.manager.switch_to(IntroScene(
                            players=self.players,
                            p1_char=self.p1_selection,
                            p2_char=p2_char
                        ))
                else:
                    # Check character slots
                    for slot_btn, slot_container, char_id in self.char_slots:
                        if e.ui_element == slot_btn:
                            if self.players == 1:
                                if self.p1_selection == char_id:
                                    self.p1_selection = None # Toggle off
                                else:
                                    self.p1_selection = char_id
                            else:
                                if self.p1_selection == char_id:
                                    self.p1_selection = None # Toggle off
                                elif self.p2_selection == char_id:
                                    self.p2_selection = None # Toggle off
                                elif not self.p1_selection:
                                    self.p1_selection = char_id
                                elif not self.p2_selection:
                                    if char_id != self.p1_selection:
                                        self.p2_selection = char_id
                                    else:
                                        # Should not happen with above logic, but for safety
                                        self._show_warning("Character already selected by P1.")
                                else:
                                    # Both selected, reset and pick for P1? Or just ignore.
                                    # Let's reset P1.
                                    self.p1_selection = char_id
                                    self.p2_selection = None
                                    
                            self._update_selection_label()
                            self._update_slot_highlights()
                            self._refresh_description()

                            if char_id in (self.p1_selection, self.p2_selection):
                                self.anim_char_id = char_id
                                self.anim_timer = self.anim_duration

    def _show_warning(self, message):
        if self.message_window:
            self.message_window.kill()
        self.message_window = pygame_gui.windows.UIMessageWindow(
            rect=scaled_rect(440, 300, 400, 200),
            html_message=message,
            manager=self.ui_manager,
            window_title="Warning"
        )

    def _char_summary_html(self, char_id):
        data = CHAR_DATA[char_id]
        skill_desc = {
            "homerun": "높은 데미지의 투사체를 던집니다.",
            "invincible_knockback": "5초 동안 무적이 되며 적을 밀어냅니다.",
            "buff_x2": "공격력과 공격속도가 2배가 됩니다."
        }.get(data["skill_type"], data["skill_type"])
        passive_desc = PASSIVE_DESC.get(char_id, "")

        html = (
            f"<font color='#ffe066' size=4><b>{data['name']}</b></font>"
            f"  HP {data['hp']} | SPD {data['speed']} | {data['attack_type']}"
            f"<br>스킬: {skill_desc}"
        )
        if passive_desc:
            html += f"<br>{passive_desc}"
        return html

    def _refresh_description(self):
        """1명만 골랐을 때는 그 캐릭터 설명만, 2인 모드에서 둘 다 골랐을 때는
        두 캐릭터 설명에 이어 공통 대시/2인 협동 기술 설명까지 함께 보여줍니다.
        아무도 선택하지 않았으면 박스 자체를 숨겨서, 선택하는 순간 박스가
        "나타나는" 것 자체로 눈에 띄게 만듭니다."""
        has_selection = bool(self.p1_selection or self.p2_selection)

        if not has_selection:
            self.desc_box.hide()
            return

        if self.players == 2 and self.p1_selection and self.p2_selection:
            html = (
                self._char_summary_html(self.p1_selection)
                + "<br><br>"
                + self._char_summary_html(self.p2_selection)
                + f"<br><br>{DASH_DESC}<br>{COMBO_DESC}"
            )
        else:
            char_id = self.p1_selection or self.p2_selection
            html = self._char_summary_html(char_id) + f"<br>{DASH_DESC}"

        self.desc_box.set_text(html)
        self.desc_box.show()

        # 처음 나타나는 순간뿐 아니라 내용이 바뀔 때마다(P1→P2 선택 등) 박스
        # 테두리가 잠깐 반짝이도록 해서, 바뀐 내용을 놓치지 않게 합니다.
        self.anim_desc_pulse = True
        self.anim_timer = self.anim_duration

    def _update_selection_label(self):
        p1_name = CHAR_DATA[self.p1_selection]["name"] if self.p1_selection else "NONE"
        if self.players == 1:
            self.selection_label.set_text(f"P1: {p1_name}")
            self.selection_label.change_object_id("#badge_1p")
        else:
            p2_name = CHAR_DATA[self.p2_selection]["name"] if self.p2_selection else "NONE"
            self.selection_label.set_text(f"P1: {p1_name} / P2: {p2_name}")
            self.selection_label.change_object_id("#badge_2p")

    def _update_slot_highlights(self):
        for slot_btn, slot_container, char_id in self.char_slots:
            if char_id == self.p1_selection or char_id == self.p2_selection:
                slot_container.change_object_id("@selected_slot")
            else:
                slot_container.change_object_id("@rank_normal_panel")

    def update(self, time_delta):
        self.ui_manager.update(time_delta)
        if self.anim_timer > 0:
            self.anim_timer = max(0.0, self.anim_timer - time_delta)

    def draw(self, screen):
        screen.fill((15, 15, 20))
        self.ui_manager.draw_ui(screen)
        self._draw_select_pulse(screen)
        self._draw_desc_pulse(screen)

    def _draw_pulse_ring(self, screen, target_rect, margin_max=18, width=4, border_radius=6):
        """target_rect 주위로 퍼져나가며 옅어지는 링 효과를 그리는 공용 헬퍼."""
        progress = 1.0 - (self.anim_timer / self.anim_duration)
        margin = int(margin_max * progress)
        alpha = max(0, int(255 * (1.0 - progress)))

        glow_rect = target_rect.inflate(margin * 2, margin * 2)
        glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(
            glow_surf, (255, 210, 60, alpha),
            glow_surf.get_rect(), width=width, border_radius=border_radius
        )
        screen.blit(glow_surf, glow_rect.topleft)

    def _draw_select_pulse(self, screen):
        """방금 선택한 캐릭터 카드 주위로 퍼져나가며 옅어지는 링 효과를 그립니다."""
        if self.anim_timer <= 0 or self.anim_char_id is None:
            return

        target_rect = None
        for slot_btn, slot_container, char_id in self.char_slots:
            if char_id == self.anim_char_id:
                target_rect = slot_container.get_abs_rect()
                break

        if target_rect is None:
            return

        self._draw_pulse_ring(screen, target_rect, margin_max=18, width=4, border_radius=6)

    def _draw_desc_pulse(self, screen):
        """설명 박스가 나타나거나 내용이 바뀔 때, 박스 테두리 주위로 같은 방식의
        링 효과를 그려서 사용자가 놓치지 않고 알아챌 수 있게 합니다."""
        if self.anim_timer <= 0 or not self.anim_desc_pulse:
            return
        if not self.desc_box.visible:
            return

        target_rect = self.desc_box.get_abs_rect()
        self._draw_pulse_ring(screen, target_rect, margin_max=10, width=5, border_radius=8)
