# audio_describer/ui/explore_scene_options_dialog.py
from ..i18n_setup import _
import wx

class ExploreSceneOptionsDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=_("Explore Scene Options"), style=wx.DEFAULT_DIALOG_STYLE)

        # --- CORRECTED SIZER AND PARENTING LOGIC ---
        
        # 1. A top-level sizer for the dialog itself
        dialog_sizer = wx.BoxSizer(wx.VERTICAL)

        # 2. A single main panel that is a child of the dialog
        panel = wx.Panel(self)
        
        # 3. A sizer for the panel's contents
        panel_sizer = wx.BoxSizer(wx.VERTICAL)

        # -- Duration setting (Widgets are children of the panel) --
        duration_sizer = wx.BoxSizer(wx.HORIZONTAL)
        duration_label = wx.StaticText(panel, label=_("Analysis Duration (seconds):"))
        duration_sizer.Add(duration_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.duration_spin = wx.SpinCtrl(panel, value="3", min=1, max=10, initial=3)
        self.duration_spin.SetToolTip(_("The length of the video clip to analyze, in seconds."))
        duration_sizer.Add(self.duration_spin, 1, wx.EXPAND)
        
        # Add the duration sizer to the panel's sizer
        panel_sizer.Add(duration_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # -- Optional prompt (Widgets are children of the panel) --
        prompt_label = wx.StaticText(panel, label=_("Optional: Specific things to focus on:"))
        panel_sizer.Add(prompt_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
        self.prompt_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 60))
        self.prompt_text.SetToolTip(_("Example: 'Focus on the expressions of the people' or 'Describe the text on any signs'"))
        
        # Add the prompt widget to the panel's sizer
        panel_sizer.Add(self.prompt_text, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # 4. Set the sizer for the panel
        panel.SetSizer(panel_sizer)
        
        # 5. Add the panel to the dialog's main sizer
        dialog_sizer.Add(panel, 1, wx.EXPAND)
        
        # -- Buttons (These are children of the dialog `self`) --
        button_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        ok_button = self.FindWindowById(wx.ID_OK)
        ok_button.SetLabel(_("&Analyze Scene"))
        ok_button.SetDefault()
        
        # Add the button sizer to the dialog's main sizer
        dialog_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        # 6. Set the final sizer for the dialog
        self.SetSizerAndFit(dialog_sizer)
        self.CentreOnParent()
    
    def GetValues(self):
        """Returns the selected duration and optional prompt."""
        return {
            "duration": self.duration_spin.GetValue(),
            "prompt": self.prompt_text.GetValue().strip()
        }