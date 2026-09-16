from core.scene_manager import SceneManager
from scenes.title_scene import TitleScene
from utils.sound_manager import init_sound

if __name__ == "__main__":
    init_sound()
    manager = SceneManager()
    manager.switch_to(TitleScene())
    manager.run()