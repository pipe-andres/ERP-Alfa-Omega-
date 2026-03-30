from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

class UIButton(ttk.Button):
    def __init__(self, parent, text: str, command: Optional[Callable]=None, style: Optional[str]=None, **kwargs):
        super().__init__(parent, text=text, command=command, style=style or 'TButton', **kwargs)
