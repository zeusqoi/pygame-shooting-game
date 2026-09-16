import pygame
import cv2
from core.scene_manager import Scene
import config

class EndingScene(Scene):
    def __init__(self, kills, video_path="assets/videos/mission_complete.mp4"):
        super().__init__()
        self.kills = kills
        self.switched = False
        self.input_delay = 3.0  # ✅ 3초 동안 입력 무시

        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.frame_delay = 1.0 / self.fps
        self.time_acc = 0
        self.current_frame = None
        self.done = False

        if not self.cap.isOpened():
            print(f"엔딩 영상 로드 실패: {video_path}")
            self.done = True

    def handle_events(self, events):
        for e in events:
            if e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
                if not self.switched and self.input_delay <= 0:  # ✅ 3초 지나야 스킵 가능
                    self.cap.release()
                    self.done = True
                    self._go_to_title()

    def update(self, time_delta):
        if self.input_delay > 0:
            self.input_delay -= time_delta  # ✅ 타이머 감소
            
        if self.done:
            return

        self.time_acc += time_delta
        if self.time_acc >= self.frame_delay:
            self.time_acc = 0
            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                self.done = True
                self._go_to_title()
                return

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
            self.current_frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

    def _go_to_title(self):
        if self.switched:
            return
        self.switched = True
        from scenes.title_scene import TitleScene
        self.manager.switch_to(TitleScene())

    def draw(self, screen):
        if self.current_frame:
            screen.blit(self.current_frame, (0, 0))
        else:
            screen.fill((0, 0, 0))

        skip_txt = config.small_font.render("Press any key to skip", True, (200, 200, 200))
        screen.blit(skip_txt, (config.SCREEN_WIDTH - skip_txt.get_width() - 20,
                                config.SCREEN_HEIGHT - skip_txt.get_height() - 20))