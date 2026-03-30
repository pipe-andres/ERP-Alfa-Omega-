# diseño/scrollbars.py
from tkinter import ttk

def agregar_scrollbar(tree, frame):
    """
    Agrega scrollbars vertical y horizontal a un ttk.Treeview dentro de 'frame'.
    """
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(xscrollcommand=hsb.set)
    hsb.pack(side="bottom", fill="x")
