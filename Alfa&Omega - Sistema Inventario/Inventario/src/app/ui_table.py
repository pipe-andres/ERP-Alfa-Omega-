from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional

class UITable(ttk.Treeview):
    """Componente tabla reutilizable. Provee métodos de carga y paginado."""
    def __init__(self, parent, columns: List[str], **kwargs):
        super().__init__(parent, columns=columns, show='headings', **kwargs)
        for c in columns:
            self.heading(c, text=c)
            self.column(c, anchor='w')

    def load_rows(self, rows: List[tuple]):
        self.delete(*self.get_children())
        for r in rows:
            self.insert('', 'end', values=r)

    def clear(self):
        self.delete(*self.get_children())
