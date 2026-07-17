# audio_describer/utils/sound_player.py
import os
import threading

try:
    import pygame
    LIBRARIES_AVAILABLE = True
except (ImportError, AttributeError, Exception) as e:
    LIBRARIES_AVAILABLE = False

from .logger import app_logger
from .. import config

MIXER_INITIALIZED = False

def _initialize_mixer():
    global MIXER_INITIALIZED
    if not LIBRARIES_AVAILABLE or MIXER_INITIALIZED:
        return
    try:
        pygame.mixer.init()
        MIXER_INITIALIZED = True
        app_logger.info("SoundPlayer: Pygame mixer initialized successfully.")
    except pygame.error as e:
        app_logger.error(f"Pygame mixer could not be initialized: {e}")
        MIXER_INITIALIZED = False

# NEW FUNCTION: Allows safe re-initialization after pygame.quit()
def reinitialize_mixer():
    """
    Re-initializes the pygame mixer if it has been shut down.
    This is necessary after another part of the app calls pygame.quit().
    """
    global MIXER_INITIALIZED
    if not LIBRARIES_AVAILABLE:
        return

    # pygame.mixer.get_init() returns None if it's not initialized
    if not pygame.mixer.get_init():
        app_logger.info("SoundPlayer: Mixer was not initialized. Attempting to re-initialize...")
        MIXER_INITIALIZED = False # Force _initialize_mixer to run
        _initialize_mixer()
    else:
        app_logger.info("SoundPlayer: Mixer is already initialized.")


def _play_in_thread(sound_path):
    """Internal function to play a sound file in a separate thread."""
    try:
        sound = pygame.mixer.Sound(sound_path)
        sound.play()
        while pygame.mixer.get_busy():
            pygame.time.delay(100)
    except Exception as e:
        app_logger.error(f"Failed to play sound: {e}", exc_info=True)

def play(sound_identifier: str, is_full_path=False):
    """
    Plays a sound in a non-blocking way.

    Notification sounds (e.g. "start.mp3") are loaded straight from the
    notifs/ folder next to the app. Pass is_full_path=True to play an
    arbitrary file (e.g. a generated TTS preview) from its own path instead.
    """
    if not MIXER_INITIALIZED:
        app_logger.warning(f"Skipping playback ('{sound_identifier}') because mixer is not initialized.")
        return

    sound_path = sound_identifier if is_full_path else os.path.join(config.get_notifs_dir(), sound_identifier)

    if not os.path.exists(sound_path):
        app_logger.error(f"Sound file not found at path '{sound_path}'. Cannot play.")
        return

    thread = threading.Thread(target=_play_in_thread, args=(sound_path,), daemon=True)
    thread.start()

# --- Initialize on import ---
_initialize_mixer()
