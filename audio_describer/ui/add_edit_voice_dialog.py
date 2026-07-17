# audio_describer/ui/add_edit_voice_dialog.py
import wx
from ..i18n_setup import _
from .accessibility_utils import set_control_accessible_name

OPENAI_BASE_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "coral", "ash", "ballad", "sage"]

class AddEditVoiceDialog(wx.Dialog):
    def __init__(self, parent, title, name="", base_voice="alloy", speed=1.0, instructions=""):
        super().__init__(parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Preset Name
        name_label = wx.StaticText(panel, label=_("Preset Name:"))
        main_sizer.Add(name_label, 0, wx.ALL | wx.EXPAND, 5)
        self.name_text_ctrl = wx.TextCtrl(panel, value=name)
        main_sizer.Add(self.name_text_ctrl, 0, wx.ALL | wx.EXPAND, 5)

        # Base OpenAI Voice
        base_voice_label = wx.StaticText(panel, label=_("Base OpenAI Voice:"))
        main_sizer.Add(base_voice_label, 0, wx.ALL | wx.EXPAND, 5)
        self.base_voice_choice = wx.Choice(panel, choices=OPENAI_BASE_VOICES)
        self.base_voice_choice.SetStringSelection(base_voice)
        main_sizer.Add(self.base_voice_choice, 0, wx.ALL | wx.EXPAND, 5)

        # --- NEW: Speed Control Slider ---
        speed_sizer = wx.BoxSizer(wx.HORIZONTAL)
        speed_label = wx.StaticText(panel, label=_("Speed:"))
        speed_sizer.Add(speed_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        # We use a large range (25-400) for the slider to represent 0.25x to 4.0x speed
        self.speed_slider = wx.Slider(panel, value=int(speed * 100), minValue=25, maxValue=400)
        speed_sizer.Add(self.speed_slider, 1, wx.ALIGN_CENTER_VERTICAL, 0)
        self.speed_value_label = wx.StaticText(panel, label=f"{speed:.2f}x", size=(40, -1))
        speed_sizer.Add(self.speed_value_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        main_sizer.Add(speed_sizer, 0, wx.EXPAND | wx.ALL, 5)
        # --- END NEW ---

        # Instructional Prompt
        instructions_label = wx.StaticText(panel, label=_("Instructions (for Tone, Emotion, etc.):"))
        main_sizer.Add(instructions_label, 0, wx.ALL | wx.EXPAND, 5)
        self.instructions_text_ctrl = wx.TextCtrl(panel, value=instructions, style=wx.TE_MULTILINE, size=(-1, 80))
        self.instructions_text_ctrl.SetToolTip(_("Describe the desired tone. Example: 'Speak in a cheerful and positive tone.'"))
        main_sizer.Add(self.instructions_text_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        panel.SetSizer(main_sizer)

        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        dialog_sizer.Add(panel, 1, wx.EXPAND | wx.ALL, 5)
        
        button_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        save_button = self.FindWindowById(wx.ID_OK)
        if save_button:
            save_button.SetLabel(_("&Save"))
            save_button.SetDefault()
        
        dialog_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        self.SetSizerAndFit(dialog_sizer)
        self.SetMinSize((450, 400))
        self.CentreOnParent()

        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wx.ID_OK)
        self.speed_slider.Bind(wx.EVT_SLIDER, self.OnSpeedChange)
        self.name_text_ctrl.SetFocus()

    def OnSpeedChange(self, event):
        speed_val = self.speed_slider.GetValue() / 100.0
        self.speed_value_label.SetLabel(f"{speed_val:.2f}x")

    def OnSave(self, event):
        if not self.name_text_ctrl.GetValue().strip():
            wx.MessageBox(_("A preset name is required."), _("Input Required"), wx.OK | wx.ICON_WARNING, self)
            return
        self.EndModal(wx.ID_OK)

    def GetVoiceData(self):
        return {
            "name": self.name_text_ctrl.GetValue().strip(),
            "base_voice": self.base_voice_choice.GetStringSelection(),
            "speed": self.speed_slider.GetValue() / 100.0,
            "instructions": self.instructions_text_ctrl.GetValue().strip()
        }