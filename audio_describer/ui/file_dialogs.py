from audio_describer.i18n_setup import _
import os
import wx
import re

from audio_describer import config
from audio_describer.ui.accessibility_utils import speak_message

def is_valid_url(url, is_youtube=False):
    """Checks if the given string is a structurally valid URL."""
    if not url:
        return False
    
    if is_youtube:
        # Regex for standard YouTube video URLs (watch?v=), shortened URLs (youtu.be/), live URLs, and shorts URLs.
        regex = re.compile(
            r'^(https?://)?(www\.)?(youtube\.com/watch\?v=[\w-]+|youtu\.be/[\w-]+|youtube\.com/live/[\w-]+|youtube\.com/shorts/[\w-]+).*$',
            re.IGNORECASE
        )
    else:
        # General URL regex
        regex = re.compile(
            r'^(?:http|ftp)s?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
    return re.match(regex, url) is not None

def show_open_video_dialog(parent_window, wildcard_str):
    """
    Shows a file dialog to select a local video file.
    Returns the selected file path or None if canceled.
    """
    # Mark dialog title for translation
    dialog_title = _("Open Local Video File")
    # Mark speak message for translation, use formatting
    speak_message(_("%s dialog.") % dialog_title)
    with wx.FileDialog(
        parent_window,
        # Message and title are arguments to wx.FileDialog, use the translated string
        message=dialog_title,
        wildcard=wildcard_str,
        style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
    ) as file_dialog:
        if file_dialog.ShowModal() == wx.ID_CANCEL:
            # Mark speak message for translation
            speak_message(_("File selection cancelled."))
            return None
        path = file_dialog.GetPath()
        # Mark speak message for translation, handle formatting for the filename
        speak_message(_("File selected: %s") % os.path.basename(path)) # Announce only filename
        return path

def show_url_input_dialog(parent_window, title, initial_message="Enter URL:", is_youtube=False):
    """
    Shows a dialog to input a URL, validates it, and re-prompts on failure.
    Returns the entered URL string or None if canceled.
    """
    speak_message(_("%s dialog.") % title)

    translated_initial_message = _(initial_message)
    translated_title = _(title)

    while True:
        with wx.TextEntryDialog(parent_window, translated_initial_message, translated_title) as text_entry_dialog:
            text_entry_dialog.SetSize((500, -1))

            if text_entry_dialog.ShowModal() == wx.ID_CANCEL:
                speak_message(_("URL input cancelled."))
                return None

            url = text_entry_dialog.GetValue().strip()

            if not url:
                speak_message(_("No URL entered."))
                return None

            if is_valid_url(url, is_youtube=is_youtube):
                speak_message(_("URL entered."))
                return url
            else:
                error_title = _("Invalid URL")
                if is_youtube:
                    error_message = _(
                        "The YouTube URL you entered does not appear to be valid.\n\n"
                        "Please use a valid format, such as:\n"
                        "youtube.com/watch?v=VIDEO_ID\n"
                        "youtu.be/VIDEO_ID\n"
                        "youtube.com/shorts/VIDEO_ID"
                    )
                else:
                    error_message = _(
                        "The URL you entered does not appear to be valid.\n\n"
                        "Please check the format (e.g., it should start with 'http://' or 'https://')."
                    )
                wx.MessageBox(error_message, error_title, wx.OK | wx.ICON_ERROR, parent_window)
                speak_message(f"{error_title}. {error_message}")

# Example usage (not run directly, but for testing within this file if needed):
if __name__ == '__main__':
    app = wx.App(False)
    # Mark frame title for translation in the test block
    frame = wx.Frame(None, title=_("Test Dialogs"))
    frame.Show()

    # Test open file dialog
    # selected_file = show_open_video_dialog(frame, config.SUPPORTED_VIDEO_FORMATS)
    # if selected_file:
    #     # Mark print statement for translation
    #     print(_("Selected file: %s") % selected_file)
    # else:
    #     # Mark print statement for translation
    #     print(_("File selection cancelled."))

    # Test URL input dialog
    # Mark the literal strings passed as arguments for translation *at the call site*
    entered_url = show_url_input_dialog(frame, _("Enter YouTube URL"), _("Paste YouTube video link:"))
    if entered_url:
        # Mark print statement for translation
        print(_("Entered URL: %s") % entered_url)
    else:
        # Mark print statement for translation
        print(_("URL input cancelled."))
    
    app.MainLoop()