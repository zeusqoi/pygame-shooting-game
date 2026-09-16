import pygame
import cv2
from core.scene_manager import Scene
import config

class IntroScene(Scene):
    def __init__(self, players=1, p1_char="choi", p2_char=None, video_path="assets/videos/run.mp4"):
        super().__init__()
        self.players = players
        self.p1_char = p1_char
        self.p2_char = p2_char

        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.frame_delay = 1.0 / self.fps
        self.time_acc = 0
        self.current_frame = None
        self.done = False

        if not self.cap.isOpened():
            print(f"동영상 로드 실패: {video_path}")
            self.done = True

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
                self.cap.release()
                self.done = True
                self._go_to_game()

    def update(self, time_delta):
        if self.done:
            return

        self.time_acc += time_delta
        if self.time_acc >= self.frame_delay:
            self.time_acc = 0
            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                self.done = True
                self._go_to_game()
                return

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            self.current_frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

    def _go_to_game(self):
        from scenes.game_scene import GameScene
        self.manager.switch_to(GameScene(
            players=self.players,
            p1_char=self.p1_char,
            p2_char=self.p2_char
        ))

    def draw(self, screen):
        if self.current_frame:
            screen.blit(self.current_frame, (0, 0))
        else:
            screen.fill((0, 0, 0))

        skip_txt = config.small_font.render("Press any key to skip", True, (200, 200, 200))
        screen.blit(skip_txt, (config.SCREEN_WIDTH - skip_txt.get_width() - 20,
                                config.SCREEN_HEIGHT - skip_txt.get_height() - 20))