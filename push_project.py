import wx

class ProjectControl(wx.Panel):
    def __init__(self, parent, projects):
        super().__init__(parent)
        self.projects = projects

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        # List of projects
        self.listbox = wx.ListBox(self, choices=self.projects, style=wx.LB_SINGLE)
        sizer.Add(self.listbox, 1, wx.EXPAND | wx.ALL, 5)

        # Plus icon for "create" (use standard art provider)
        bmp_plus = wx.ArtProvider.GetBitmap(wx.ART_PLUS, wx.ART_BUTTON, (24,24))
        self.add_btn = wx.BitmapButton(self, bitmap=bmp_plus)
        sizer.Add(self.add_btn, 0, wx.ALL, 5)
        self.add_btn.Bind(wx.EVT_BUTTON, self.on_add_project)

        # Push button to show selected project
        self.push_btn = wx.Button(self, label="Push")
        sizer.Add(self.push_btn, 0, wx.ALL, 5)
        self.push_btn.Bind(wx.EVT_BUTTON, self.on_push)

        self.SetSizer(sizer)

    def on_add_project(self, event):
        dlg = wx.TextEntryDialog(self, "Enter new project name:", "New Project")
        if dlg.ShowModal() == wx.ID_OK:
            new_name = dlg.GetValue()
            if new_name and new_name not in self.projects:
                self.projects.append(new_name)
                self.listbox.Append(new_name)
                self.listbox.SetSelection(len(self.projects)-1)
        dlg.Destroy()

    def on_push(self, event):
        idx = self.listbox.GetSelection()
        if idx != wx.NOT_FOUND:
            project_name = self.projects[idx]
            wx.MessageBox(f"Selected project:\n{project_name}", "Project Selected", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("No project selected.", "Error", wx.OK | wx.ICON_ERROR)

# Usage in your main Frame
class MainFrame(wx.Frame):
    def __init__(self, project_names):
        super().__init__(None, title="Select/Create Project")
        panel = ProjectControl(self, project_names)
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.GetSizer().Add(panel, 1, wx.EXPAND | wx.ALL, 10)
        self.Fit()
        self.Show()

if __name__ == "__main__":
    app = wx.App(False)
    projects = ["Project A", "Project B", "Project C"]
    frame = MainFrame(projects)
    app.MainLoop()
