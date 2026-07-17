import logging
import os
import sys
from audio_describer import config

_log_file_path = ""

def get_app_root_for_logging():
    """
    Gets the application's root directory for logging purposes.
    This is a self-contained version of the function in config.py to avoid imports.
    """
    if getattr(sys, 'frozen', False):
        # For a frozen app (like PyInstaller), the root is where the executable is.
        return os.path.dirname(sys.executable)
    else:
        # In source mode, the root is the main project directory, one level up
        # from this 'utils' directory.
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def get_log_file_path():
    """Returns the full path to the application's log file."""
    global _log_file_path
    if not _log_file_path:
        _log_file_path = os.path.join(get_app_root_for_logging(), config.LOG_FILE)
    return _log_file_path

def setup_logger():
    """Sets up the application logger in the app's root directory."""
    global _log_file_path
    
    log_dir = get_app_root_for_logging()
    _log_file_path = os.path.join(log_dir, config.LOG_FILE)

    log_format = '%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s'

    # Clear previous handlers to prevent duplication
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.handlers.clear()

    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format=log_format,
        handlers=[
            logging.FileHandler(_log_file_path, mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(config.APP_NAME_BASE_UNTRANSLATED)
    logger.info(f"Logger initialized. Log file at: {_log_file_path}")
    return logger

def update_log_level():
    """Updates the logger's level based on the current settings."""
    # This now safely imports config_model as there is no circular dependency.
    from audio_describer.models import config_model

    logger = logging.getLogger(config.APP_NAME_BASE_UNTRANSLATED)
    level_str = config_model.get_setting("logging_level") or config.LOG_LEVEL

    if level_str.upper() == "DISABLED":
        logger.disabled = True
    else:
        logger.disabled = False
        level = getattr(logging, level_str.upper(), logging.INFO)
        logger.setLevel(level)
        for handler in logging.getLogger().handlers:
            handler.setLevel(level)
        logger.info(f"Logger level set to {level_str.upper()}")

app_logger = setup_logger()