# audio_describer/ui/add_edit_prompt_dialog.py
from ..i18n_setup import _
import wx
from .accessibility_utils import set_control_accessible_name

class AddEditPromptDialog(wx.Dialog):
    def __init__(self, parent, title, prompt_name="", prompt_text=""):
        super().__init__(parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        # A main sizer for the dialog itself
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # A panel for the main content area
        panel = wx.Panel(self)
        panel_sizer = wx.BoxSizer(wx.VERTICAL)

        # Prompt Name (child of panel, added to panel's sizer)
        name_label = wx.StaticText(panel, label=_("Preset Name:"))
        panel_sizer.Add(name_label, 0, wx.ALL | wx.EXPAND, 5)
        self.name_text_ctrl = wx.TextCtrl(panel, value=prompt_name)
        set_control_accessible_name(self.name_text_ctrl, _("A short, descriptive name for the prompt preset."))
        panel_sizer.Add(self.name_text_ctrl, 0, wx.ALL | wx.EXPAND, 5)

        # Prompt Text (child of panel, added to panel's sizer)
        prompt_label = wx.StaticText(panel, label=_("Prompt Text:"))
        panel_sizer.Add(prompt_label, 0, wx.ALL | wx.EXPAND, 5)
        self.prompt_text_ctrl = wx.TextCtrl(panel, value=prompt_text, style=wx.TE_MULTILINE, size=(-1, 150))
        set_control_accessible_name(self.prompt_text_ctrl, _("The full text of the prompt to be sent to the AI."))
        panel_sizer.Add(self.prompt_text_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        panel.SetSizer(panel_sizer)

        # Add the content panel to the dialog's main sizer
        main_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 5)

        # Buttons. These are children of the dialog `self` and are managed by the main_sizer.
        button_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        save_button = self.FindWindowById(wx.ID_OK)
        if save_button:
            save_button.SetLabel(_("&Save"))
            save_button.SetDefault()
        
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        self.SetSizerAndFit(main_sizer)
        self.SetMinSize((400, 300))
        self.CentreOnParent()

        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wx.ID_OK)
        self.name_text_ctrl.SetFocus()

    def OnSave(self, event):
        name = self.name_text_ctrl.GetValue().strip()
        text = self.prompt_text_ctrl.GetValue().strip()

        if not name or not text:
            wx.MessageBox(_("Both a preset name and prompt text are required."), _("Input Required"), wx.OK | wx.ICON_WARNING, self)
            return

        self.EndModal(wx.ID_OK)

    def GetPromptData(self):
        """Returns the entered prompt data."""
        return {
            "name": self.name_text_ctrl.GetValue().strip(),
            "prompt": self.prompt_text_ctrl.GetValue().strip()
        }