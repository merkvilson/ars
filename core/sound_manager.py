import pygame
import os
sound_path = os.path.join("res", "sounds")

def play_sound(name, volume=0.5):  # Default to half volume; pass a different value if needed
    if name == "hover": volume = 0.2
    elif name == "back": volume = 0.06
    elif name == "hover2": volume = 0.6
    elif name == "delete-obj": volume = 0.6
    sound = pygame.mixer.Sound(os.path.join(sound_path,f"{name}.mp3"))
    sound.set_volume(volume)
    sound.play()  # Non-blocking; overlaps fine