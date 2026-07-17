# audio_describer/ui/export_options_dialog.py
import wx
from ..i18n_setup import _

class ExportOptionsDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=_("Export Options"), style=wx.DEFAULT_DIALOG_STYLE)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        panel = wx.Panel(self)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)

        # Combined export options using a single RadioBox
        # The choices implicitly define the category and format
        self.export_choices_map = [
            ("mp3_ducked", _("MP3 Audio (Descriptions mixed with original video)")),
            ("srt", _("SRT Subtitle File (Descriptions as subtitles)")),
            ("txt_line", _("Plain Text File (.txt) (Descriptions line-by-line)")),
        ]
        
        # Extract only the display strings for the RadioBox
        display_choices = [item[1] for item in self.export_choices_map]

        self.export_radiobox = wx.RadioBox(
            panel, 
            label=_("Select Export Format"), 
            choices=display_choices, 
            majorDimension=1, 
            style=wx.RA_SPECIFY_COLS
        )
        self.export_radiobox.SetSelection(0) # Default to MP3
        panel_sizer.Add(self.export_radiobox, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(panel_sizer)
        main_sizer.Add(panel, 1, wx.EXPAND)
        
        button_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        ok_button = self.FindWindowById(wx.ID_OK)
        ok_button.SetLabel(_("&Continue"))
        ok_button.SetDefault()
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        self.SetSizerAndFit(main_sizer)
        self.CentreOnParent()

    def GetValues(self):
        selected_idx = self.export_radiobox.GetSelection()
        format_key = self.export_choices_map[selected_idx][0]

        if format_key == "mp3_ducked":
            return {"category": "av", "format": "mp3_ducked"}
        elif format_key == "srt":
            return {"category": "text", "format": "srt"}
        elif format_key == "txt_line":
            return {"category": "text", "format": "txt_line"}
        else:
            # Fallback, though should not happen with fixed choices
            return {"category": "text", "format": "srt"} # Default if something goes wrong