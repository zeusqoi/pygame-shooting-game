import os
import json
from pathlib import Path
import pygame

BASE_DIR = Path(__file__).resolve().parent.parent
SOUND_DIR = BASE_DIR / "assets" / "sounds"
SETTINGS_PATH = BASE_DIR / "settings.json"

_sound_cache = {}

# ---------------------------------------------------------
# 배경음(BGM) / 효과음(SFX) 마스터 볼륨
# 각 play_sound / play_music 호출에 지정된 개별 볼륨에 곱해지는 배율입니다.
# (0.0 ~ 1.0), 값은 settings.json에 저장되어 다음 실행 시에도 유지됩니다.
# ---------------------------------------------------------
bgm_volume = 0.5
sfx_volume = 0.6

# 현재 재생 중인 BGM의 "원래(개별) 볼륨" - 슬라이더로 마스터 볼륨을 바꿀 때
# 이미 재생 중인 음악에도 즉시 반영하기 위해 기억해둡니다.
_current_music_base_volume = 0.5


def load_settings():
    global bgm_volume, sfx_volume
    try:
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            bgm_volume = float(data.get("bgm_volume", bgm_volume))
            sfx_volume = float(data.get("sfx_volume", sfx_volume))
    except Exception as e:
        print(f"[SOUND ERROR] 설정 로드 실패: {e}")


def save_settings():
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump({"bgm_volume": bgm_volume, "sfx_volume": sfx_volume}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[SOUND ERROR] 설정 저장 실패: {e}")


def get_bgm_volume():
    return bgm_volume


def get_sfx_volume():
    return sfx_volume


def set_bgm_volume(value, persist=True):
    global bgm_volume
    bgm_volume = max(0.0, min(1.0, value))
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(_current_music_base_volume * bgm_volume)
    except Exception as e:
        print(f"[SOUND ERROR] BGM 볼륨 적용 실패: {e}")
    if persist:
        save_settings()


def set_sfx_volume(value, persist=True):
    global sfx_volume
    sfx_volume = max(0.0, min(1.0, value))
    if persist:
        save_settings()


# 모듈이 처음 임포트될 때 저장된 볼륨 설정을 불러옵니다.
load_settings()


def init_sound():
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            print("[SOUND] mixer initialized")
    except Exception as e:
        print(f"[SOUND ERROR] mixer init failed: {e}")


def _resolve_sound_path(sound_path):
    if os.path.isabs(sound_path):
        return sound_path

    if os.path.exists(sound_path):
        return sound_path

    candidate = SOUND_DIR / sound_path
    return str(candidate)


def play_sound(sound_path, volume=0.6, loops=0):
    try:
        if not sound_path:
            return None

        if not pygame.mixer.get_init():
            pygame.mixer.init()
            print("[SOUND] mixer initialized inside play_sound")

        resolved_path = _resolve_sound_path(sound_path)

        if not os.path.exists(resolved_path):
            print(f"[SOUND ERROR] 효과음 파일 없음: {resolved_path}")
            return None

        if resolved_path not in _sound_cache:
            _sound_cache[resolved_path] = pygame.mixer.Sound(resolved_path)

        sound = _sound_cache[resolved_path]
        sound.set_volume(volume * sfx_volume)
        channel = sound.play(loops=loops)

        print(f"[SOUND] played: {resolved_path}")
        return channel

    except Exception as e:
        print(f"[SOUND ERROR] 효과음 재생 실패: {e}")
        return None


def stop_channel(channel):
    try:
        if channel is not None:
            channel.stop()
    except Exception as e:
        print(f"[SOUND ERROR] 채널 정지 실패: {e}")


def play_music(music_path, volume=0.5, loops=-1):
    global _current_music_base_volume
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            print("[MUSIC] mixer initialized inside play_music")

        resolved_path = _resolve_sound_path(music_path)

        if not os.path.exists(resolved_path):
            print(f"[MUSIC ERROR] 음악 파일 없음: {resolved_path}")
            return

        _current_music_base_volume = volume

        pygame.mixer.music.load(resolved_path)
        pygame.mixer.music.set_volume(volume * bgm_volume)
        pygame.mixer.music.play(loops)

        print(f"[MUSIC] playing: {resolved_path}")

    except Exception as e:
        print(f"[MUSIC ERROR] 음악 재생 실패: {e}")


def stop_music():
    try:
        pygame.mixer.music.stop()
    except Exception as e:
        print(f"[MUSIC ERROR] 음악 정지 실패: {e}")
