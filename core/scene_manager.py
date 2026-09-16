import pygame
import sys
import config
from core.globals import screen, clock

class Scene:
    def __init__(self):
        self.manager = None

    def handle_events(self, events): pass
    def update(self, time_delta): pass
    def draw(self, screen): pass

class SceneManager:
    def __init__(self):
        self.scene = None

    def switch_to(self, scene):
        self.scene = scene
        self.scene.manager = self

    def run(self):
        running = True
        while running:
            time_delta = clock.tick(config.FPS) / 1000.0
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
            
            if self.scene:
                self.scene.handle_events(events)
                self.scene.update(time_delta)
                self.scene.draw(screen)
            
            pygame.display.flip()
        pygame.quit()
        sys.exit()
