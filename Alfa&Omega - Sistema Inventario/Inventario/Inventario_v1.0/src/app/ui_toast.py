from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from threading import Timer
from typing import Optional

class UIToast(tk.Toplevel):
    def __init__(self, parent, message: str, duration: int = 3):
        super().__init__(parent)
        self.wm_overrideredirect(True)
        label = ttk.Label(self, text=message)
        label.pack(padx=8, pady=4)
        self.after(duration*1000, self.destroy)
