import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame

sound_path = os.path.join("res", "sounds")

_MIXER_READY = False
_SOUND_CACHE: dict[str, pygame.mixer.Sound] = {}


def _ensure_mixer() -> bool:
    global _MIXER_READY
    if _MIXER_READY:
        return True
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        _MIXER_READY = True
        return True
    except Exception:
        return False


def _load_sound_cached(name: str) -> pygame.mixer.Sound | None:
    snd = _SOUND_CACHE.get(name)
    if snd is not None:
        return snd

    # Keep it simple: prefer mp3, fallback to wav.
    for ext in (".mp3", ".wav"):
        path = os.path.join(sound_path, f"{name}{ext}")
        if not os.path.exists(path):
            continue
        try:
            snd = pygame.mixer.Sound(path)
            _SOUND_CACHE[name] = snd
            return snd
        except Exception:
            return None
    return None

def play_sound(name, volume=0.5):  # Default to half volume; pass a different value if needed
    if name == "hover": volume = 0.4
    elif name == "back": volume = 0.1
    elif name == "hover2": volume = 0.6
    elif name == "delete-obj": volume = 0.6
    elif name == "click": volume = 0.06
    elif name == "revert": volume = 0.2
    if not _ensure_mixer():
        return
    sound = _load_sound_cached(name)
    if sound is None:
        return
    try:
        sound.set_volume(volume)
        sound.play()  # Non-blocking; overlaps fine
    except Exception:
        return