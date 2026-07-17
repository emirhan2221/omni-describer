# audio_describer/utils/update_checker.py
import wx
import urllib.request
import json
import os
import sys
import tempfile
import zipfile
import subprocess
from packaging.version import parse
from ..utils.logger import app_logger
from ..utils import sound_player
from .. import config # <-- FIX: Added import for config to get the new UPDATER_URL

def get_app_path():
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        import __main__
        return os.path.abspath(__main__.__file__)

def get_app_dir():
    return os.path.dirname(get_app_path())

def check_for_updates(parent_frame, current_version, version_url, download_url, lang_code, _):
    try:
        # version_url points at the GitHub "latest release" API, which returns JSON.
        # A User-Agent is required or GitHub answers 403.
        req = urllib.request.Request(version_url, headers={"User-Agent": "OmniDescriber-Updater"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
        remote_version = data.get("tag_name", "").lstrip("v").strip()
        if remote_version and parse(remote_version) > parse(current_version):
            wx.CallAfter(_show_update_prompt, parent_frame, remote_version, current_version, download_url, lang_code, _)
    except Exception as e:
        app_logger.error(f"Update check failed: {e}", exc_info=True)

def _show_update_prompt(parent_frame, remote_version, current_version, download_url, lang_code, _):
    sound_player.play("update.mp3")
    msg = (_("A new version ({}) is available. You have version {}.\n\n"
           "Would you like to download and install it now?").format(remote_version, current_version))
    title = _("Update Available")
    user_choice = wx.MessageBox(msg, title, wx.YES_NO | wx.ICON_QUESTION, parent=parent_frame)
    if user_choice == wx.YES:
        _initiate_update_and_exit(parent_frame, download_url, lang_code, _)

def _initiate_update_and_exit(parent_frame, download_url, lang_code, _):
    progress_dialog = wx.ProgressDialog(
        _("Downloading Update"), _("Downloading..."), 
        maximum=100, parent=parent_frame, style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE
    )
    try:
        temp_dir = tempfile.gettempdir()
        zip_path = os.path.join(temp_dir, "update.zip")
        with urllib.request.urlopen(download_url) as response, open(zip_path, 'wb') as out_file:
            total_size = int(response.info().get('Content-Length', -1))
            bytes_so_far = 0
            chunk_size = 8192
            while True:
                chunk = response.read(chunk_size)
                if not chunk: break
                out_file.write(chunk)
                bytes_so_far += len(chunk)
                if total_size > 0:
                    percent = int(bytes_so_far * 100 / total_size)
                    progress_dialog.Update(percent)
        progress_dialog.Destroy()
        
        app_dir = get_app_dir()
        app_path = get_app_path()
        updater_path = os.path.join(app_dir, "updater.exe")

        # --- START: FIX for missing updater component ---
        if not os.path.exists(updater_path):
            app_logger.warning("Updater component not found at '%s'. Attempting to download it.", updater_path)
            
            # Inform the user that a required component is being downloaded.
            wx.MessageBox(
                _("The updater component seems to be missing. The application will now attempt to download the necessary updater to proceed."),
                _("Updater Missing"),
                wx.OK | wx.ICON_INFORMATION,
                parent_frame
            )
            
            try:
                # Assumes UPDATER_URL is defined in your config.py, e.g., "https://yoursite.com/updater.exe"
                with urllib.request.urlopen(config.UPDATER_URL) as response, open(updater_path, 'wb') as out_file:
                    out_file.write(response.read())
                
                app_logger.info("Successfully downloaded standalone updater to '%s'", updater_path)

                # Final check to ensure the file was actually created before proceeding.
                if not os.path.exists(updater_path):
                    raise IOError("Updater file not found even after a successful download attempt.")

            except Exception as e:
                # If the download fails, show a detailed error and stop the update process.
                app_logger.error("Failed to download the standalone updater: %s", e, exc_info=True)
                wx.MessageBox(
                    _("Could not download the required updater component. The update cannot proceed.\n\nPlease try again later or contact support.\n\nError: {}").format(e),
                    _("Update Error"),
                    wx.OK | wx.ICON_ERROR,
                    parent_frame
                )
                return # Stop the update.
        # --- END: FIX ---

        # If we reach this point, updater_path is guaranteed to exist.
        parent_pid = os.getpid()
            
        command = [
            updater_path, # No need for the complex ternary logic if we always expect an .exe
            zip_path, 
            app_dir, 
            app_path, 
            lang_code,
            str(parent_pid)
        ]
        
        subprocess.Popen(command)
        
        app_logger.info("Update initiated. Triggering fast app exit.")
        app = wx.GetApp()
        app.is_updating = True
        parent_frame.Close()
    except Exception as e:
        if progress_dialog: progress_dialog.Destroy()
        wx.MessageBox(_("Failed to download or apply update: {}").format(e), _("Update Error"), wx.OK | wx.ICON_ERROR, parent_frame)