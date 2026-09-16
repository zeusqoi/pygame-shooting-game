import pygame
import pygame_gui
import config
from core.globals import theme_path, db, current_user
from core.scene_manager import Scene
from utils.layout import scaled_rect

class RankingScene(Scene):
    def __init__(self, back_scene_class=None):
        super().__init__()
        self.back_scene_class = back_scene_class
        self.ui_manager = pygame_gui.UIManager((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), theme_path)
        
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(40, 30, 600, 100),
            text="HALL OF FAME",
            manager=self.ui_manager,
            object_id="#menu_title"
        )
        
        self.btn_all = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(560, 40, 80, 40),
            text="ALL",
            manager=self.ui_manager,
            object_id="@tab_active"
        )
        self.btn_1p = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(650, 40, 80, 40),
            text="1P",
            manager=self.ui_manager,
            object_id="@tab_inactive"
        )
        self.btn_2p = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(740, 40, 80, 40),
            text="2P",
            manager=self.ui_manager,
            object_id="@tab_inactive"
        )
        
        self.btn_back = pygame_gui.elements.UIButton(
            relative_rect=scaled_rect(1100, 40, 140, 40),
            text="BACK",
            manager=self.ui_manager,
            object_id="@tab_inactive"
        )
        
        self.my_rank_label = pygame_gui.elements.UILabel(
            relative_rect=scaled_rect(40, 100, 1200, 40),
            text="",
            manager=self.ui_manager,
            object_id="#ranking_header_text"
        )
        
        self.header_panel = pygame_gui.elements.UIPanel(
            relative_rect=scaled_rect(40, 150, 1200, 50),
            manager=self.ui_manager,
            starting_height=1,
            object_id="@rank_normal_panel"
        )
        pygame_gui.elements.UILabel(scaled_rect(20, 0, 100, 50), "RANK", self.ui_manager, container=self.header_panel, object_id="#ranking_header_text")
        pygame_gui.elements.UILabel(scaled_rect(200, 0, 300, 50), "OPERATIVE", self.ui_manager, container=self.header_panel, object_id="#ranking_header_text")
        pygame_gui.elements.UILabel(scaled_rect(700, 0, 200, 50), "MODE", self.ui_manager, container=self.header_panel, object_id="#ranking_header_text")
        pygame_gui.elements.UILabel(scaled_rect(950, 0, 200, 50), "SCORE", self.ui_manager, container=self.header_panel, object_id="#ranking_header_text")

        self.scroll_container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=scaled_rect(40, 210, 1200, 550),
            manager=self.ui_manager
        )
        
        self.current_mode = None
        self.panels = []
        self.load_rankings()

    def load_rankings(self):
        for p in self.panels:
            p.kill()
        self.panels.clear()
        
        import core.globals as globals
        my_rank, my_score = db.get_user_ranking(globals.current_user, self.current_mode)
        mode_text = self.current_mode if self.current_mode else "ALL"
        if my_rank is not None:
            self.my_rank_label.set_text(f"Operative: {globals.current_user}  |  Mode: {mode_text}  |  Rank: {my_rank}  |  Best Score: {my_score:,}")
        else:
            self.my_rank_label.set_text(f"Operative: {globals.current_user}  |  Mode: {mode_text}  |  No Record")
            
        ranks = db.get_rankings(mode=self.current_mode, limit=None)
        
        y_offset = 0
        panel_height = 60
        spacing = 10
        
        for idx, row in enumerate(ranks):
            player_name, score, game_mode, play_date = row
            rank = idx + 1
            
            panel_id = "@rank_normal_panel"
            text_id = "#rank_normal_text"
            if rank == 1:
                panel_id = "@rank_gold_panel"
                text_id = "#rank_gold_text"
            elif rank == 2:
                panel_id = "@rank_silver_panel"
                text_id = "#rank_silver_text"
            elif rank == 3:
                panel_id = "@rank_bronze_panel"
                text_id = "#rank_bronze_text"
                
            panel = pygame_gui.elements.UIPanel(
                relative_rect=scaled_rect(0, y_offset, 1170, panel_height),
                manager=self.ui_manager,
                container=self.scroll_container,
                object_id=panel_id
            )
            self.panels.append(panel)
            
            pygame_gui.elements.UILabel(scaled_rect(20, 0, 100, panel_height), str(rank), self.ui_manager, container=panel, object_id=text_id)
            pygame_gui.elements.UILabel(scaled_rect(200, 0, 300, panel_height), player_name, self.ui_manager, container=panel, object_id=text_id)
            
            mode_badge = "#badge_1p" if game_mode == "Single" else "#badge_2p"
            mode_display = "1P" if game_mode == "Single" else "2P"
            pygame_gui.elements.UILabel(scaled_rect(760, 15, 80, 30), mode_display, self.ui_manager, container=panel, object_id=mode_badge)
            
            pygame_gui.elements.UILabel(scaled_rect(950, 0, 200, panel_height), f"{score:,}", self.ui_manager, container=panel, object_id=text_id)
            
            y_offset += panel_height + spacing
            
        self.scroll_container.set_scrollable_area_dimensions((1170, max(y_offset, 550)))

    def handle_events(self, events):

        for e in events:
            self.ui_manager.process_events(e)
            if e.type == pygame_gui.UI_BUTTON_PRESSED:
                if e.ui_element == self.btn_back:
                    if self.back_scene_class:
                        self.manager.switch_to(self.back_scene_class())
                    else:
                        from scenes.title_scene import TitleScene
                        self.manager.switch_to(TitleScene())
                elif e.ui_element == self.btn_all:
                    self.current_mode = None
                    self._update_tabs(self.btn_all)
                elif e.ui_element == self.btn_1p:
                    self.current_mode = "Single"
                    self._update_tabs(self.btn_1p)
                elif e.ui_element == self.btn_2p:
                    self.current_mode = "Duo"
                    self._update_tabs(self.btn_2p)

    def _update_tabs(self, active_btn):
        self.btn_all.change_object_id("@tab_active" if self.btn_all == active_btn else "@tab_inactive")
        self.btn_1p.change_object_id("@tab_active" if self.btn_1p == active_btn else "@tab_inactive")
        self.btn_2p.change_object_id("@tab_active" if self.btn_2p == active_btn else "@tab_inactive")
        self.load_rankings()

    def update(self, time_delta):
        self.ui_manager.update(time_delta)

    def draw(self, screen):
        screen.fill((15, 15, 20)) 
        self.ui_manager.draw_ui(screen)
