# character_select_scene.py

import pygame
import pygame_gui
import os
import config
from core.globals import theme_path, CHAR_DATA, main_bg_img
from core.scene_manager import Scene
from utils.ui_utils import draw_bg_aspect_ratio
from scenes.intro_scene import IntroScene

class CharacterSelectScene(Scene):
    def __init__(self, players=1):
        super().__init__()
        self.ui_manager = pygame_gui.UIManager((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), theme_path)
        self.players = players
        self.p1_selection = None
        self.p2_selection = None
        
        # 1. Top Bar
        self.setup_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((40, 30), (300, 80)),
            text="SETUP",
            manager=self.ui_manager,
            object_id="#menu_title"
        )
        self.btn_back = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((1100, 30), (140, 40)),
            text="BACK",
            manager=self.ui_manager,
            object_id="@tab_inactive"
        )
        
        # 2. Select Mode Section
        self.mode_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((40, 110), (1200, 150)),
            manager=self.ui_manager,
            object_id="@rank_normal_panel"
        )
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((20, 10), (300, 40)),
            text="SELECT MODE",
            manager=self.ui_manager,
            container=self.mode_panel,
            object_id="#ranking_header_text"
        )
        self.btn_1p = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((20, 50), (400, 70)),
            text="1 PLAYER",
            manager=self.ui_manager,
            container=self.mode_panel,
            object_id="@tab_active" if self.players == 1 else "@tab_inactive"
        )
        self.btn_2p = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((440, 50), (400, 70)),
            text="2 PLAYERS",
            manager=self.ui_manager,
            container=self.mode_panel,
            object_id="@tab_active" if self.players == 2 else "@tab_inactive"
        )
        
        # 3. Select Character Section
        self.char_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect((40, 270), (1200, 410)),
            manager=self.ui_manager,
            object_id="@rank_normal_panel"
        )
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((20, 10), (400, 40)),
            text="SELECT CHARACTER",
            manager=self.ui_manager,
            container=self.char_panel,
            object_id="#ranking_header_text"
        )
        self.selection_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect((700, 10), (480, 40)),
            text="P1: NONE",
            manager=self.ui_manager,
            container=self.char_panel,
            object_id="#badge_1p"
        )
        
        # Character Slots
        self.char_slots = []
        self.char_images = []
        slot_width = 240
        slot_height = 240
        num_chars = len(CHAR_DATA)
        total_slots_width = num_chars * slot_width
        spacing = (1200 - total_slots_width) // (num_chars + 1)
        x_offset = spacing
        y_offset = 50
        
        for char_id, data in CHAR_DATA.items():
            # Use UIPanel as the container for the slot
            slot_container = pygame_gui.elements.UIPanel(
                relative_rect=pygame.Rect((x_offset, y_offset), (slot_width, slot_height)),
                manager=self.ui_manager,
                container=self.char_panel,
                object_id="@rank_normal_panel"
            )
            
            # Transparent Button on top for clicks
            slot_btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((0, 0), (slot_width, slot_height)),
                text="",
                manager=self.ui_manager,
                container=slot_container,
                object_id="@transparent_btn" # We should define this or use a style that has no bg
            )
            
            # Image
            char_prefix = data["name"].lower()
            img_path = f"assets/images/{char_prefix}_default.png"
            if os.path.exists(img_path):
                try:
                    img_surf = pygame.image.load(img_path).convert_alpha()
                    img_surf = pygame.transform.scale(img_surf, (120, 120))
                    self.char_images.append(img_surf)
                    pygame_gui.elements.UIImage(
                        relative_rect=pygame.Rect((60, 20), (120, 120)),
                        image_surface=img_surf,
                        manager=self.ui_manager,
                        container=slot_container
                    )
                except Exception as e:
                    print(f"Failed to load {img_path}: {e}")
            
            # Name Label
            pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect((0, 160), (slot_width, 40)),
                text=data["name"],
                manager=self.ui_manager,
                container=slot_container,
                object_id="#rank_normal_text"
            )
            
            self.char_slots.append((slot_btn, slot_container, char_id))
            x_offset += slot_width + spacing
            
        # Description Box
        self.desc_box = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((20, 310), (1160, 80)),
            html_text="Select a character to see details.",
            manager=self.ui_manager,
            container=self.char_panel,
            object_id="#char_desc_text"
        )
            
        # 4. Start Game Button
        self.btn_start = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((440, 690), (400, 70)),
            text="START GAME",
            manager=self.ui_manager,
            object_id="@green_btn"
        )
        self.message_window = None

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
                elif e.ui_element == self.btn_2p:
                    self.players = 2
                    self.btn_1p.change_object_id("@tab_inactive")
                    self.btn_2p.change_object_id("@tab_active")
                    self._update_selection_label()
                    self._update_slot_highlights()
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
                            if char_id in [self.p1_selection, self.p2_selection]:
                                self._update_description(char_id)

    def _show_warning(self, message):
        if self.message_window:
            self.message_window.kill()
        self.message_window = pygame_gui.windows.UIMessageWindow(
            rect=pygame.Rect((440, 300), (400, 200)),
            html_message=message,
            manager=self.ui_manager,
            window_title="Warning"
        )

    def _update_description(self, char_id):
        data = CHAR_DATA[char_id]
        skill_desc = {
            "homerun": "높은 데미지의 투사체를 던집니다.",
            "invincible_knockback": "5초 동안 무적이 되며 적을 밀어냅니다.",
            "buff_x2": "공격력과 공격속도가 2배가 됩니다."
        }.get(data["skill_type"], data["skill_type"])
        
        html = f"<b>{data['name']}</b> | HP: {data['hp']} | Speed: {data['speed']} | Attack: {data['attack_type']}<br>{skill_desc}"
        self.desc_box.set_text(html)

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

    def draw(self, screen):
        screen.fill((15, 15, 20)) 
        self.ui_manager.draw_ui(screen)
