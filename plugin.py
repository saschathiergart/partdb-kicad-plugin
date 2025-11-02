from typing import (
    Callable,
    List,
    Optional,
    Type,
    Tuple
)
import os
import threading
import pcbnew
import json
import wx
import wx.dataview as dv
import sys
import collections
from pcbnew import (
    BOARD, 
    FOOTPRINT,
    PCB_FIELD,
    ActionPlugin,
    SETTINGS_MANAGER,
    Refresh,
        GetBoard,
        LoadBoard,
        SaveBoard
)
import requests
from .partdb.part import Part
from .partdb.api import PartDB

import logging

plugin_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(plugin_dir, "plugin.log")

logging.basicConfig(
    # filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d]: %(message)s',
    filemode='a',  # append mode
    handlers=[ 
        # logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr)  # Also print to console
    ]
)

logger = logging.getLogger(__name__)

STORAGE_LOCATION_FIELD_NAME = "Storage_Location"
PARTDB_ID_FIELD_NAME = "PartDB_ID"
MPN_FIELD_NAME = "MPN"
#TODO:Remove
# class SortableKey:
#     """Wrapper that allows None values to be compared"""
#     def __init__(self, value):
#         self.value = value
    
#     def __lt__(self, other):
#         # None is always "greater" (sorts last)
#         if self.value is None:
#             return False
#         if other.value is None:
#             return True
#         return self.value < other.value
    
#     def __eq__(self, other):
#         return self.value == other.value
    
#     def __le__(self, other):
#         return self < other or self == other
    
#     def __gt__(self, other):
#         return not (self <= other)
    
#     def __ge__(self, other):
#         return not (self < other)
    
#     def __repr__(self):
#         return f"SortableKey({self.value})"

class FootprintData:
    footprint:FOOTPRINT
    _partdb_part:Optional[Part] = None
    
    """Data holder for footprint and associated PartDB part."""
    def __init__(self, footprint:FOOTPRINT, partdb_part:Optional[Part]=None) -> None:
        self.footprint = footprint
        self._partdb_part = partdb_part
    
    @property
    def reference(self) -> str:
        reference:PCB_FIELD = self.footprint.Reference()
        return reference.GetText()
    
    @property
    def partdb_part(self) -> Optional[Part]:
        return self._partdb_part
    
    @partdb_part.setter
    def partdb_part(self, partdb_part:Part) -> None :
        self._partdb_part = partdb_part

    @property
    def partdb_id(self) -> Optional[str]:
        partdb_field:Optional[PCB_FIELD] = self.footprint.GetFieldByName(PARTDB_ID_FIELD_NAME)
        if not partdb_field:
            return None
        partdb_id:str = partdb_field.GetText()
        return partdb_id if partdb_id != "" else None
    
    @property
    def mpn(self) -> Optional[str]:
        mpn_field:PCB_FIELD = self.footprint.GetFieldByName(MPN_FIELD_NAME)
        if not mpn_field:
            return None
        mpn = mpn_field.GetText()
        return mpn if mpn != "" else None 
    
    @property
    def storage_location(self) -> Optional[str]:
        if not self.partdb_part:
            return None
        part_lots = self.partdb_part.partLots
        if len(part_lots) > 0:
            # return 'YES DUMMY '
            return ', '.join([part_lot.storage_location.name for part_lot in part_lots])
    
    @property
    def amount(self) -> Optional[str]:
        if not self.partdb_part:
            return None
        part_lots = self.partdb_part.partLots
        if len(part_lots) > 0:
            return str(sum(part_lot.amount for part_lot in part_lots))
    
    def update_storage_location(self) -> None:
        '''
        Updates or creates a Field STORAGE_LOCATION_FIELD_NAME 
        '''
        logging.debug(f'attempting to update or create Storage Location field on part {self.reference}')
        storage_location = self.storage_location
        if self.footprint.HasFieldByName(STORAGE_LOCATION_FIELD_NAME):
            # Field exists, update it
            self.footprint.SetField(STORAGE_LOCATION_FIELD_NAME, storage_location if storage_location else '')
            return
        
        field = PCB_FIELD(self.footprint,self.footprint.GetNextFieldId(),STORAGE_LOCATION_FIELD_NAME)
        field.SetText(str(storage_location))
        field.SetVisible(False)
        self.footprint.AddField(field)


# ============================================================================
# PANEL: API Configuration
# ============================================================================
class ApiConfigPanel(wx.Panel):
    """Panel for API URL, token, and synchronize button"""
    
    def __init__(self, parent:wx.Window, api_url: str, token: str, on_sync_click: Callable):
        super().__init__(parent)
        self.on_sync_click = on_sync_click
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # API URL
        url_label = wx.StaticText(self, label="PartDB API URL:")
        sizer.Add(url_label, 0, wx.LEFT | wx.TOP | wx.RIGHT, 10)
        
        self.api_url_ctrl = wx.TextCtrl(self, value=api_url)
        self.api_url_ctrl.SetMinSize((480, 25))
        sizer.Add(self.api_url_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Token
        token_label = wx.StaticText(self, label="Token:")
        sizer.Add(token_label, 0, wx.LEFT | wx.TOP | wx.RIGHT, 10)
        
        self.token_ctrl = wx.TextCtrl(self, value=token, style=wx.TE_PASSWORD)
        self.token_ctrl.SetMinSize((480, 25))
        sizer.Add(self.token_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        
        # Button row
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.AddStretchSpacer()

        #TODO:Connect Button
        # self.sync_btn = wx.Button(self, label="Connect")
        # self.sync_btn.Bind(wx.EVT_BUTTON, self._on_connect_click)
        # button_sizer.Add(self.sync_btn, 0, wx.ALL | wx.CENTER, 5)
        
        self.sync_btn = wx.Button(self, label="Synchronize")
        self.sync_btn.Bind(wx.EVT_BUTTON, self._on_sync_btn_click)
        button_sizer.Add(self.sync_btn, 0, wx.ALL | wx.CENTER, 5)
        
        self.save_config_btn = wx.Button(self, label="Save Configuration")
        self.save_config_btn.Bind(wx.EVT_BUTTON, lambda evt: self.on_sync_click("save_config", self.get_values()))
        button_sizer.Add(self.save_config_btn, 0, wx.ALL | wx.CENTER, 5)
        
        sizer.Add(button_sizer, 0, wx.EXPAND | wx.ALL, 10)
        
        self.SetSizer(sizer)
    
    def _on_sync_btn_click(self, event):
        self.on_sync_click("sync", self.get_values())
    
    def get_values(self) -> Tuple[str, str]:
        """Return current API URL and token"""
        return (self.api_url_ctrl.GetValue().strip(), self.token_ctrl.GetValue().strip())
    
    def set_values(self, api_url: str, token: str):
        """Update displayed values"""
        self.api_url_ctrl.SetValue(api_url)
        self.token_ctrl.SetValue(token)


# ============================================================================
# PANEL: Footprint Table
# ============================================================================
class FootprintTablePanel(wx.Panel):
    """Displays the BOM tree with footprint data"""
    footprints_data_grouped:dict[Tuple[str,str],List[FootprintData]]
    
    def __init__(self, parent:wx.Window, footprints_data_grouped: dict):
        super().__init__(parent)
        self.footprints_data_grouped = footprints_data_grouped
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title and label
        title = wx.StaticText(self, label="Components")
        title_font = title.GetFont()
        title_font.MakeBold()
        title.SetFont(title_font)
        sizer.Add(title, 0, wx.ALL, 10)
        
        # Tree list control
        self.tree = dv.TreeListCtrl(
            self, style=wx.TR_DEFAULT_STYLE | wx.TR_FULL_ROW_HIGHLIGHT
        )
        self.tree.AppendColumn("References", width=170)
        self.tree.AppendColumn("Qty", width=60)
        self.tree.AppendColumn("MPN", width=80)
        self.tree.AppendColumn("PartDB ID", width=150)
        self.tree.AppendColumn("Storage Location", width=150)
        self.tree.AppendColumn("Storage Amount", width=100)
        
        sizer.Add(self.tree, 1, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(sizer)
        
        self.update_table()
    
    def update_table(self):
        """Refresh the tree with current footprint data"""

        self.tree.DeleteAllItems()
        root = self.tree.GetRootItem()
        if not root:
            root = self.tree.AppendItem(None, "BOM")
        
        for (mpn, partdb_id), footprints in sorted(
            self.footprints_data_grouped.items(),
            key=lambda x: (x[0][0] is None, x[0][0], x[0][1] is None, x[0][1])
        ):
            refs = ", ".join(fp.reference for fp in footprints)
            qty = str(len(footprints))
            
            parent_item = self.tree.AppendItem(root, refs)
            self.tree.SetItemText(parent_item, 1, qty)
            self.tree.SetItemText(parent_item, 2, mpn or "")
            self.tree.SetItemText(parent_item, 3, partdb_id or "")
            
            storage_location = footprints[0].storage_location or ""
            storage_amount = str(footprints[0].amount) if footprints[0].amount else ""
            self.tree.SetItemText(parent_item, 4, storage_location)
            self.tree.SetItemText(parent_item, 5, storage_amount)
            
            for fp in footprints:
                child_item = self.tree.AppendItem(parent_item, fp.reference)
                self.tree.SetItemText(child_item, 1, "1")
                self.tree.SetItemText(child_item, 2, fp.mpn or "")
                self.tree.SetItemText(child_item, 3, fp.partdb_id or "")
                self.tree.SetItemText(child_item, 4, fp.storage_location or "")
                self.tree.SetItemText(child_item, 5, str(fp.amount) if fp.amount else "")
        
        self.tree.Expand(root)


# ============================================================================
# PANEL: Action Buttons
# ============================================================================
class ActionButtonPanel(wx.Panel):
    """Buttons: Save to Board, Close"""
    
    def __init__(self, parent, on_save: Callable, on_close: Callable):
        super().__init__(parent)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddStretchSpacer()
        
        save_btn = wx.Button(self, label="Save to Board")
        save_btn.Bind(wx.EVT_BUTTON, lambda evt: on_save())
        sizer.Add(save_btn, 0, wx.ALL | wx.CENTER, 5)
        
        close_btn = wx.Button(self, label="Close")
        close_btn.Bind(wx.EVT_BUTTON, lambda evt: on_close())
        sizer.Add(close_btn, 0, wx.ALL | wx.CENTER, 5)
        
        self.SetSizer(sizer)


# ============================================================================
# PANEL: Status Bar
# ============================================================================
class StatusBarPanel(wx.Panel):
    """Simple status display at bottom"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.status_text = wx.StaticText(self, label="Ready")
        status_font = self.status_text.GetFont()
        status_font.MakeItalic()
        self.status_text.SetFont(status_font)
        
        sizer.Add(self.status_text, 0, wx.ALL, 10)
        self.SetSizer(sizer)
    
    def set_status(self, message: str):
        """Update status message"""
        self.status_text.SetLabel(message)


# ============================================================================
# MAIN FRAME: Controller
# ============================================================================
class PartDBPlugin(wx.Frame):
    """Main frame that coordinates panels and manages PartDB instance"""
    footprints_data_grouped:dict[Tuple[Optional[str],Optional[str]],List[FootprintData]] = collections.defaultdict(list)

    def __init__(self):
        super().__init__(None, title="PartDB Plugin", size=(900, 700))
        
        # Get board and load config
        self.board = pcbnew.GetBoard()
        api_url, token = self._load_config()
        
        # Initialize data
        self.partdb: Optional[PartDB] = None
        self._load_board_footprints()
        
        # Create main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(self, label="PartDB Synchronizer")
        title_font = title.GetFont()
        title_font.MakeBold()
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL, 10)
        
        # API Config Panel
        self.api_panel = ApiConfigPanel(
            self, 
            api_url=api_url, 
            token=token,
            on_sync_click=self._on_api_panel_action
        )
        main_sizer.Add(self.api_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        # Footprint Table Panel
        self.table_panel = FootprintTablePanel(self, self.footprints_data_grouped)
        main_sizer.Add(self.table_panel, 1, wx.EXPAND | wx.ALL, 5)
        
        # Action Buttons Panel
        self.action_panel = ActionButtonPanel(
            self,
            on_save=self._on_save,
            on_close=self._on_close
        )
        main_sizer.Add(self.action_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        # Status Bar Panel
        self.status_panel = StatusBarPanel(self)
        main_sizer.Add(self.status_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(main_sizer)
        self.Bind(wx.EVT_CLOSE, self._on_close)
    
    def _on_api_panel_action(self, action: str, values: Tuple[str, str]):
        """Handle actions from API panel"""
        api_url, token = values
        
        if action == "save_config":
            self._save_config(api_url, token)
            self.status_panel.set_status("Configuration saved")
        
        elif action == "sync":
            # Validate
            if not api_url:
                wx.MessageBox("Please enter a PartDB API URL", "Warning", wx.OK | wx.ICON_WARNING)
                self.status_panel.set_status("Error: API URL is empty")
                return
            
            if not token:
                wx.MessageBox("Please enter a PartDB API Token", "Warning", wx.OK | wx.ICON_WARNING)
                self.status_panel.set_status("Error: API Token is empty")
                return
            
            # Disable button and show progress
            self.api_panel.sync_btn.Enable(False)
            self.status_panel.set_status("Synchronizing...")
            
            # Run sync in background thread
            thread = threading.Thread(target=self._sync_thread, args=(api_url, token))
            thread.daemon = True
            thread.start()
    
    def _sync_thread(self, api_url: str, token: str):
        """Background thread for synchronization"""
        try:
            # Create PartDB instance
            self.partdb = PartDB(bearer=token, base_url=api_url)
            
            # Fetch and update footprint data
            for (mpn, partdb_id), footprints in self.footprints_data_grouped.items():
                if not partdb_id:
                    continue
                
                partdb_part = self.partdb.get_part_from_id(partdb_id)
                if partdb_part:
                    for fp in footprints:
                        fp.partdb_part = partdb_part
            
            logging.debug(f"Sync complete: {len(self.footprints_data_grouped)} groups")
            wx.CallAfter(self._on_sync_complete)
        
        except Exception as e:
            logging.exception("Sync failed")
            wx.CallAfter(self._on_sync_error, str(e))
    
    def _on_sync_complete(self):
        """Called in main thread after sync succeeds"""
        self.table_panel.update_table()
        self.status_panel.set_status("Synchronization completed successfully")
        self.api_panel.sync_btn.Enable(True)
    
    def _on_sync_error(self, error: str):
        """Called in main thread after sync fails"""
        self.status_panel.set_status(f"Error: {error}")
        self.api_panel.sync_btn.Enable(True)
        wx.MessageBox(f"Sync failed:\n{error}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_save(self):
        """Save footprint data back to board"""
        try:
            self.status_panel.set_status("Saving to board...")
            for (mpn, partdb_id), footprints in self.footprints_data_grouped.items():
                for fp in footprints:
                    fp.update_storage_location()
            pcbnew.Refresh()
            self.status_panel.set_status("Saved to board successfully")
        except Exception as e:
            logging.exception("Save failed")
            self.status_panel.set_status(f"Error: {e}")
            wx.MessageBox(f"Save failed:\n{e}", "Error", wx.OK | wx.ICON_ERROR)
    
    def _on_close(self, event=None):
        """Close the frame"""
        logging.debug("Closing PartDB Plugin")
        self.Destroy()
    
    def _load_board_footprints(self) -> None:
        """Load footprints from board"""
        self.footprints_data_grouped = collections.defaultdict(list)
        
        pcbnew_footprints: List[pcbnew.FOOTPRINT] = self.board.GetFootprints()
        footprints = [
            FootprintData(fp) for fp in pcbnew_footprints 
            if not fp.IsExcludedFromBOM()
        ]
        
        for fp in footprints:
            key = (fp.mpn, fp.partdb_id)
            self.footprints_data_grouped[key].append(fp)
        
        logging.debug(f"Loaded {len(footprints)} footprints")
    
    @staticmethod
    def _get_global_config_file() -> str:
        """Get config file path"""
        settings_path = SETTINGS_MANAGER.GetUserSettingsPath()
        plugin_dir = os.path.join(settings_path, "plugins", "partdb-kicad-plugin")
        os.makedirs(plugin_dir, exist_ok=True)
        return os.path.join(plugin_dir, "config.json")
    
    @staticmethod
    def _save_config(api_url: str, token: str):
        """Save configuration to file"""
        config_file = PartDBPlugin._get_global_config_file()
        config = {"api_url": api_url, "token": token}
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    @staticmethod
    def _load_config() -> Tuple[str, str]:
        """Load configuration from file"""
        config_file = PartDBPlugin._get_global_config_file()
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                return (config.get('api_url', ''), config.get('token', ''))
        
        return ('https://partdb.example.com/api', '')

# ============================================================================
# ACTION PLUGIN
# ============================================================================
class SyncStorageLocation(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "PartDB Storage Location"
        self.category = "Inventory Management"
        self.description = "Fetches Storage Locations from PartDB instance"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'icon.png')
        self.frame = None
    
    def Run(self):
        if self.frame and self.frame.IsShown():
            self.frame.Raise()
            return
        
        logging.debug("Launching PartDB Plugin")
        self.frame = PartDBPlugin()
        self.frame.Show()
