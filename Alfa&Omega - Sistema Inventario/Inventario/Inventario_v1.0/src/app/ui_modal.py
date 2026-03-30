from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Optional

class UIModal(tk.Toplevel):
    def __init__(self, parent, title: str = "", modal: bool = True, **kwargs):
        super().__init__(parent, **kwargs)
        self.title(title)
        self.transient(parent)
        if modal:
            self.grab_set()
        self.protocol('WM_DELETE_WINDOW', self.close)

    def close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
