# audio_describer/ui/manage_voices_dialog.py
import wx
import wx.lib.mixins.listctrl as listmix
from ..i18n_setup import _
from ..models import voice_model
from .add_edit_voice_dialog import AddEditVoiceDialog
from .accessibility_utils import set_control_accessible_name

class ManageVoicesDialog(wx.Dialog, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent):
        super().__init__(parent, title=_("Manage OpenAI Voice Presets"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, size=(700, 400))
        listmix.ListCtrlAutoWidthMixin.__init__(self)

        self.voices = voice_model.get_voices()

        self.InitUI()
        self.PopulateList()
        self.CentreOnParent()

    def InitUI(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        info_text = wx.StaticText(panel, label=_("Create and manage voice personalities for OpenAI TTS."))
        main_sizer.Add(info_text, 0, wx.ALL | wx.EXPAND, 5)

        self.voice_list_ctrl = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.voice_list_ctrl.InsertColumn(0, _("Preset Name"), width=180)
        self.voice_list_ctrl.InsertColumn(1, _("Base Voice"), width=80)
        self.voice_list_ctrl.InsertColumn(2, _("Speed"), width=60)
        self.voice_list_ctrl.InsertColumn(3, _("Instructions"), width=300)
        self.setResizeColumn(3)
        main_sizer.Add(self.voice_list_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.add_button = wx.Button(panel, label=_("&Add..."))
        self.edit_button = wx.Button(panel, label=_("&Edit..."))
        self.delete_button = wx.Button(panel, label=_("&Delete"))
        
        self.edit_button.Disable()
        self.delete_button.Disable()
        
        button_sizer.Add(self.add_button, 0, wx.ALL, 5)
        button_sizer.Add(self.edit_button, 0, wx.ALL, 5)
        button_sizer.Add(self.delete_button, 0, wx.ALL, 5)
        main_sizer.Add(button_sizer, 0, wx.ALL, 5)

        panel.SetSizer(main_sizer)
        
        dialog_sizer = wx.BoxSizer(wx.VERTICAL)
        dialog_sizer.Add(panel, 1, wx.EXPAND)
        close_button_sizer = self.CreateStdDialogButtonSizer(wx.CLOSE)
        dialog_sizer.Add(close_button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.SetSizer(dialog_sizer)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.voice_list_ctrl)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected, self.voice_list_ctrl)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnEdit, self.voice_list_ctrl)
        self.add_button.Bind(wx.EVT_BUTTON, self.OnAdd)
        self.edit_button.Bind(wx.EVT_BUTTON, self.OnEdit)
        self.delete_button.Bind(wx.EVT_BUTTON, self.OnDelete)

    def PopulateList(self):
        self.voice_list_ctrl.DeleteAllItems()
        for i, voice in enumerate(self.voices):
            index = self.voice_list_ctrl.InsertItem(i, voice.get("name", ""))
            self.voice_list_ctrl.SetItem(index, 1, voice.get("base_voice", ""))
            self.voice_list_ctrl.SetItem(index, 2, f"{voice.get('speed', 1.0):.2f}x")
            self.voice_list_ctrl.SetItem(index, 3, voice.get("instructions", ""))
            self.voice_list_ctrl.SetItemData(index, i)
        self.OnItemDeselected(None)

    def OnItemSelected(self, event):
        self.edit_button.Enable()
        self.delete_button.Enable()

    def OnItemDeselected(self, event):
        self.edit_button.Disable()
        self.delete_button.Disable()

    def OnAdd(self, event):
        with AddEditVoiceDialog(self, title=_("Add New Voice Preset")) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.voices.append(dlg.GetVoiceData())
                self.SaveChanges()
                self.PopulateList()
                self.voice_list_ctrl.SetItemState(self.voice_list_ctrl.GetItemCount() - 1, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

    def OnEdit(self, event):
        selected_idx = self.voice_list_ctrl.GetFirstSelected()
        if selected_idx == -1: return
        original_idx = self.voice_list_ctrl.GetItemData(selected_idx)
        voice = self.voices[original_idx]
        with AddEditVoiceDialog(self, title=_("Edit Voice Preset"), **voice) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.voices[original_idx] = dlg.GetVoiceData()
                self.SaveChanges()
                self.PopulateList()
                self.voice_list_ctrl.SetItemState(selected_idx, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

    def OnDelete(self, event):
        selected_idx = self.voice_list_ctrl.GetFirstSelected()
        if selected_idx == -1: return
        voice_name = self.voices[self.voice_list_ctrl.GetItemData(selected_idx)].get("name")
        msg = wx.MessageDialog(self, _("Are you sure you want to delete the preset '%s'?") % voice_name, _("Confirm Delete"), wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
        if msg.ShowModal() == wx.ID_YES:
            del self.voices[self.voice_list_ctrl.GetItemData(selected_idx)]
            self.SaveChanges()
            self.PopulateList()
        msg.Destroy()

    def SaveChanges(self):
        voice_model.set_voices(self.voices)