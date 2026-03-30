# diseño/estilo.py
from tkinter import ttk

# Color de fondo que usa tu GUI
COLOR_FONDO = "#F6F8FA"
def aplicar_estilo_treeview(tree):
    style = ttk.Style(tree)
    try: style.theme_use("clam")
    except: pass
    style.configure("Treeview", rowheight=26)
    tree.tag_configure("par", background="#FFFFFF")
    tree.tag_configure("impar", background="#F9F9F9")
    tree.tag_configure("baja", background="#FFECEC", foreground="#B20000")
    tree.tag_configure("alta", background="#EEFAF0", foreground="#0D7A2B")
    tree.tag_configure("mod",  background="#FFF8E1", foreground="#8A6D3B")
