# audio_describer/models/voice_model.py
import json
import os
from . import config_model
from ..utils.logger import app_logger

VOICES_FILE_NAME = "voices.json"
VOICES_FILE_PATH = os.path.join(config_model.APP_DATA_DIR, VOICES_FILE_NAME)

# Default presets to give the user a starting point, now with speed control.
DEFAULT_VOICES = [
    {"name": "Narrator - Standard", "base_voice": "alloy", "speed": 1.0, "instructions": "Speak in a clear, neutral, and steady narration voice."},
    {"name": "Narrator - Fast", "base_voice": "alloy", "speed": 1.2, "instructions": "Speak in a clear and neutral tone, but at a slightly faster pace."},
    {"name": "Character - Energetic", "base_voice": "nova", "speed": 1.1, "instructions": "Speak in a cheerful and positive tone, with a youthful energy."},
    {"name": "Character - Deliberate", "base_voice": "onyx", "speed": 0.85, "instructions": "Speak in a deep, resonant, and serious tone. Pace the words slowly."},
    {"name": "Whisper", "base_voice": "shimmer", "speed": 0.9, "instructions": "Speak in a soft, quiet whisper."},
]

# In-memory cache for voices
_voices_cache = []

def load_voices():
    """Loads all voice presets from the JSON file into the cache."""
    global _voices_cache
    if not os.path.exists(VOICES_FILE_PATH):
        app_logger.info(f"Voices file not found at {VOICES_FILE_PATH}. Creating with defaults.")
        _voices_cache = DEFAULT_VOICES.copy()
        save_voices()
        return

    try:
        with open(VOICES_FILE_PATH, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        # Data validation and migration: ensure all voices have the new 'speed' key
        updated = False
        for voice in loaded_data:
            if 'speed' not in voice:
                voice['speed'] = 1.0  # Add default speed to older presets
                updated = True
        
        if updated:
            app_logger.info("Updated voice presets to include new 'speed' parameter.")
            save_voices()
        
        _voices_cache = loaded_data
        
        if not _voices_cache:
            _voices_cache = DEFAULT_VOICES.copy()
            save_voices()
        app_logger.info(f"Voice presets loaded successfully from {VOICES_FILE_PATH}.")
    except (json.JSONDecodeError, IOError) as e:
        app_logger.error(f"Error loading voice presets from {VOICES_FILE_PATH}: {e}. Using default voices.")
        _voices_cache = DEFAULT_VOICES.copy()

def save_voices():
    """Saves the current state of the voices cache to the JSON file."""
    global _voices_cache
    try:
        with open(VOICES_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(_voices_cache, f, indent=4, ensure_ascii=False)
        app_logger.info(f"Voice presets saved successfully to {VOICES_FILE_PATH}.")
        return True
    except IOError as e:
        app_logger.error(f"Error saving voice presets to {VOICES_FILE_PATH}: {e}")
        return False

def get_voices():
    """Returns a list of all voice preset dictionaries."""
    if not _voices_cache:
        load_voices()
    return _voices_cache

def set_voices(voices_list):
    """Sets the entire list of voice presets and saves."""
    global _voices_cache
    if not isinstance(voices_list, list):
        app_logger.error("set_voices: provided voices is not a list.")
        return False
    _voices_cache = voices_list
    return save_voices()

def get_voice_by_name(name):
    """Finds a specific voice preset by its unique name."""
    for voice in get_voices():
        if voice.get("name") == name:
            return voice
    return None

# Initialize the cache on module load
load_voices()