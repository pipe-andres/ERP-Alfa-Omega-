# src/app/styles/theme.py
from tkinter import ttk
from typing import Literal

# Valores por defecto (claro)
COLOR_FONDO = "#F6F8FA"
COLOR_TEXT = "#222222"
THEME_MODE: Literal['light','dark'] = 'light'


def aplicar_estilo_treeview(tree):
    style = ttk.Style(tree)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("Treeview", rowheight=26, background=COLOR_FONDO, foreground=COLOR_TEXT)
    tree.tag_configure("par", background="#FFFFFF")
    tree.tag_configure("impar", background="#F9F9F9")
    tree.tag_configure("baja", background="#FFECEC", foreground="#B20000")
    tree.tag_configure("alta", background="#EEFAF0", foreground="#0D7A2B")
    tree.tag_configure("mod",  background="#FFF8E1", foreground="#8A6D3B")


def set_mode(mode: Literal['light','dark']):
    global THEME_MODE, COLOR_FONDO, COLOR_TEXT
    if mode == 'dark':
        COLOR_FONDO = "#1E1E1E"
        COLOR_TEXT = "#E6E6E6"
    else:
        COLOR_FONDO = "#F6F8FA"
        COLOR_TEXT = "#222222"
    THEME_MODE = mode
