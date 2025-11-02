import wx
import wx.dataview as dv
from collections import defaultdict

from kipy import KiCad, errors, board
from kipy.proto.common.types.base_types_pb2 import DocumentType
from kipy.board_types import Field, FootprintInstance
from partdb.api import get_part_from_id
from partdb.part import *

import logging

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")

# ----------- Example footprint model ----------------

class FootprintDataWrapper:
    reference:str
    kicad_footprint:FootprintInstance
    mpn:str
    partdb_id:int
    
    def __init__(self, footprint:FootprintInstance) -> None:
        self.kicad_footprint = footprint




class DummyField:
    def __init__(self, name, value):
        self.name = name
        self.text = self
        self.value = value

class DummyFootprintInstance:
    def __init__(self, reference, mpn, partdb_id):
        self.reference_field = DummyField('Reference', reference)
        self.texts_and_fields = [
            DummyField('MPN', mpn),
            DummyField('PartDB_ID', partdb_id),
        ]
        self.attributes = type('A', (), {"do_not_populate": False, "exclude_from_bill_of_materials": False})

# ----------- Data grouping logic -------------------
# def get_footprints(board:board.Board ):
#     footprints = board.get_footprints()
#     fp_selected:List[FootprintDataWrapper]
#     for footprint in footprints:
#         if footprint.attributes.exclude_from_bill_of_materials or footprint.attributes.do_not_populate:
#             continue
#         fp = FootprintDataWrapper(footprint)


def group_footprints(fp_selected):
    groups = defaultdict(list)
    # Group by (MPN, PartDB_ID, Value, Footprint, Datasheet)
    for fp in fp_selected:
        fields = {f.name: f.text.value.strip() if f.text and f.text.value else "" for f in fp.texts_and_fields}
        key = (
            fields.get("MPN", ""),
            fields.get("PartDB_ID", ""),
        )
        groups[key].append(fp)
    # Sort keys for display
    sorted_keys = sorted(groups.keys(), key=lambda k: (k[0].lower(), k[1].lower()))
    return [(key, groups[key]) for key in sorted_keys]

# ----------- User Interface ------------------------
class BomDialog(wx.Dialog):
    def __init__(self, parent, grouped_data):
        super().__init__(parent, title="Expandable BOM Table", size=(1200, 600))
        self.kicad = KiCad()
        self.board = self.kicad.get_board()
        self.schematic = self.kicad.get_open_documents
        self.tree = dv.TreeListCtrl(self, style=wx.TR_DEFAULT_STYLE | wx.TR_FULL_ROW_HIGHLIGHT)

        # Define columns
        self.tree.AppendColumn("Reference", width=170)
        self.tree.AppendColumn("Qty", width=60)
        self.tree.AppendColumn("MPN", width=80)
        self.tree.AppendColumn("PartDB_ID", width=80)

        self.sync_button = wx.Button(self, label="Synchronize")
        self.sync_button.Bind(wx.EVT_BUTTON, self.on_synchronize)

        self.refresh_btn = wx.Button(self, label="Refresh")
        self.refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)

        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(self.sync_button, 0, wx.ALL | wx.CENTER, 10)
        sizer.Add(self.refresh_btn, 0, wx.ALL | wx.CENTER, 10)
        self.SetSizer(sizer)

    def on_refresh(self, event):
        try:
            fp = self.board.get_footprints()
            fp_selected:List[Tuple[FootprintInstance,Optional[Field], Optional[Field]]]=[]
            for footprint in fp:
                if footprint.attributes.do_not_populate or footprint.attributes.exclude_from_bill_of_materials:
                    continue
                logging.debug(f'{footprint.Get}')
                mpn_field:Field|None = None 
                partdb_id_field:Field|None = None
                for field in footprint.texts_and_fields:
                    if isinstance(field,Field) and field.name == 'PartDB_ID':
                        partdb_id_field = field
                    elif isinstance(field,Field) and field.name == 'MPN':
                        mpn_field = field
                fp_selected.append((footprint, mpn_field, partdb_id_field))
        except BaseException as e:
            logging.exception(f'Error loading existing footprints')

        self.tree.DeleteAllItems()
        root = self.tree.GetRootItem()
        if not root:
            root = self.tree.AppendItem(None, "BOM")
        
        self.parent_items = set()  # store group items (parents)
        self.item_to_reference = {}




        # Fill tree
        for group_key, footprints in grouped_data:
            parent_ref_text = ", ".join(fp.reference_field.value for fp in footprints)
            qty_text = str(len(footprints))
            mpn, partdb_id = group_key

            parent_item = self.tree.AppendItem(root, parent_ref_text)
            self.parent_items.add(parent_item)
            self.tree.SetItemText(parent_item, 1, qty_text)
            self.tree.SetItemText(parent_item, 2, mpn)
            self.tree.SetItemText(parent_item, 3, partdb_id)

            for fp in footprints:
                child_item = self.tree.AppendItem(parent_item, fp.reference_field.value)
                self.item_to_reference[child_item] = fp.reference_field.value
                self.tree.SetItemText(child_item, 1, "1")
                self.tree.SetItemText(child_item, 2, mpn)
                self.tree.SetItemText(child_item, 3, partdb_id)
                self.item_to_reference[child_item] = fp.reference_field.value


        self.tree.Expand(root)


    def on_synchronize(self, event):
        selection = self.tree.GetSelections()
        selected_refs = set()

        def collect_children_refs(parent):
            for child in self.get_children(parent):
                ref = self.item_to_reference.get(child)
                if ref:
                    selected_refs.add(ref)

        for item in selection:
            if item in self.parent_items:
                collect_children_refs(item)
            else:
                ref = self.item_to_reference.get(item)
                if ref:
                    selected_refs.add(ref)

        logging.debug(f"Selected footprints for sync: {sorted(selected_refs)}")

    def get_children(self, parent):
        children = []
        child = self.tree.GetFirstChild(parent)
        while child.IsOk():
            children.append(child)
            child = self.tree.GetNextSibling(child)
        return children





# ----------- Demo runner: replace with KiCad objects in your plugin! ----------------
if __name__ == "__main__":
    app = wx.App()

    fp_selected = [
        DummyFootprintInstance("C1", "GRM123", "312"),
        DummyFootprintInstance("C33", "GRM123", "311"),
        DummyFootprintInstance("C38", "GRM123", "312"),
        DummyFootprintInstance("C2", "GRM200", "379"),
        DummyFootprintInstance("C8", "GRM200", "379"),
        DummyFootprintInstance("C9", "GRM200", ""),
        DummyFootprintInstance("C10", "GRM200", "")
        # ... add more for testing
    ]

    grouped_data = group_footprints(fp_selected)
    logging.debug(grouped_data)
    dlg = BomDialog(None, grouped_data)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
