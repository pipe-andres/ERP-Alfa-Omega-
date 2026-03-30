from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Optional

class UIInput(ttk.Entry):
    def __init__(self, parent, textvariable=None, width: int=20, **kwargs):
        super().__init__(parent, textvariable=textvariable, width=width, **kwargs)

    def get_value(self) -> str:
        return self.get().strip()

    def set_value(self, v: str):
        self.delete(0, 'end')
        self.insert(0, v)
